import asyncio
import json
import random
from dataclasses import asdict
from typing import Any
from typing import Literal
from typing import Optional

import aiohttp
from loguru import logger

from .data import Coordinates
from .data import Filters
from .data import Product
from .utils import get_query_id_for_search
from .utils import image_url

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
DEFAULT_RETRIES_NUM = 3
DEFAULT_ERROR_SLEEP_TIME = 5  # In seconds


class WildBerriesApiError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class WildBerriesAPI:
    """A class for asynchronous interaction with the WildBerries private API."""
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT) -> None:
        self.headers = {"User-Agent": user_agent}
        self._session: Optional[aiohttp.ClientSession] = None

    @staticmethod
    def search_data_to_products(products_json: dict) -> list[Product]:
        try:
            data = products_json.get("data").get("products")
        except AttributeError as e:
            logger.error("WildBerries API didn't return products")
            raise WildBerriesApiError("WildBerries API didn't return products")

        products = []
        for product in data:
            try:
                products.append(
                    Product(
                        id=product.get("id"),
                        price=product.get("sizes")[0].get("price").get("total") // 100,
                        name=product.get("name"),
                        image_url=image_url(product.get("id"), "BIG"),
                    )
                )
            except AttributeError as r:
                logger.error(r)
                continue
        return products

    @staticmethod
    def get_combinations(
        *products: list[Product],
        min_price: int | None = None,
        max_price: int | None = None,
    ) -> list[tuple[dict]]:
        """
        Returns clothing combinations. In *products, we list `list[Product]`.
        max_repeats - The maximum number of combinations with a single element
        """
        combined = list(
            zip(
                *[
                    [product.to_json() for product in products_list]
                    for products_list in products
                ]
            )
        )
        random.shuffle(combined)
        filtered_combinations = []
        for combination in combined:
            total_price = sum(product["price"] for product in combination)
            if min_price <= total_price <= max_price:
                filtered_combinations.append(combination)

        return filtered_combinations

    async def get_dist_id(self, coords: Coordinates) -> int:
        """
        Returns the dist_id, which is the region ID from WildBerries.
        """
        response = await self._request(
            url="https://user-geo-data.wildberries.ru/get-geo-info",
            request_method="get",
            params={
                "currency": "RUB",
                "latitude": coords.latitude,
                "longitude": coords.longitude,
            },
        )
        try:
            return response.get("destinations")[-1]
        except TypeError:
            logger.error("WildBerriesAPI didn't return dist by geo")
            return -1257786  # MOSCOW

    async def search(
        self, query: str, page: int = 1, filters: Optional[Filters] = None
    ) -> list[Product]:
        headers = {"x-queryid": get_query_id_for_search()}
        if not filters:
            filters = Filters()
        params = {
            "ab_testid": "false",
            "appType": 1,  # 1 - DESKTOP, 32 - ANDROID, 64 - IOS
            "curr": "rub",
            "dest": filters.dest,
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "spp": 30,
            "suppressSpellcheck": "false",
            "uclusters": 1,
        }
        if page != 1:
            params["page"] = page
        if filters.is_original:
            params["foriginal"] = filters.is_original
        url = "https://search.wb.ru/exactmatch/ru/common/v5/search"
        response = await self._request(
            url=url, request_method="get", params=params, headers=headers
        )
        return self.search_data_to_products(json.loads(response))

    async def _get_new_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(headers=self.headers)

    async def _get_session(self) -> Optional[aiohttp.ClientSession]:
        if self._session is None or self._session.closed:
            self._session = await self._get_new_session()

        if not self._session._loop.is_running():
            await self._session.close()
            self._session = await self._get_new_session()
        return self._session

    async def _request(
        self,
        url: str,
        request_method: Literal["get", "post"] = "get",
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        retries: int = DEFAULT_RETRIES_NUM,
        **kwargs,
    ) -> Any:
        await self._get_session()
        if request_method == "post":
            method = self._session.post
        else:
            method = self._session.get

        try:
            async with method(url=url, params=params, data=data, **kwargs) as response:
                logger.warning(response.status)
                if response.content_type == "application/json":

                    return await response.json()
                else:
                    return await response.text()
        except aiohttp.ClientError as e:
            logger.error(f"Error occupied while sending request to {url}:\n{e}")
            if retries > 0:
                await asyncio.sleep(DEFAULT_ERROR_SLEEP_TIME)
                return await self._request(
                    url, request_method, params, data, retries - 1, **kwargs
                )
            raise WildBerriesApiError(str(e))

    async def close(self):
        await self._session.close()
