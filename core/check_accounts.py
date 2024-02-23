import asyncio

import aiofiles
import aiohttp
from loguru import logger
from pyuseragents import random as random_useragent

from custom_types.formatted_account import FormattedAccount
from utils import format_account, loader, get_proxy


class DropChecker:
    def __init__(self,
                 account_data: FormattedAccount) -> None:
        self.account_data: FormattedAccount = account_data

    async def get_drop_amount(self,
                              client: aiohttp.ClientSession) -> float | None:
        response_text: None = None

        while True:
            proxy: str | None = get_proxy()

            try:
                r: aiohttp.ClientResponse = await client.get(
                    url='https://backend.smartlayer.network/airdrop/homebrew-eligibility',
                    params={
                        'address': self.account_data.address,
                        'withProof': 'true'
                    },
                    headers={
                        'User-Agent': random_useragent()
                    },
                    proxy=proxy,
                    timeout=10
                )

                response_text: str = await r.text()

                if '403 ERROR' in response_text:
                    logger.info(f'{self.account_data.address} | Rate Limit')
                    continue

                response_json: dict = await r.json(content_type=None)

                if not response_json['eligible']:
                    return

                return int(response_json['details']['amount']) / 10 ** 18

            except Exception as error:
                if response_text:
                    logger.error(f'{self.account_data.address} | Unexpected Error When Getting Drop Amount: {error}, '
                                 f'response: {response_text}')

                else:
                    logger.error(f'{self.account_data.address} | Unexpected Error When Getting Drop Amount: {error}')

    async def check_account(self) -> None:
        async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    verify_ssl=None,
                    ssl=False,
                    use_dns_cache=False,
                    ttl_dns_cache=300,
                    limit=None
                )
        ) as client:
            return await self.get_drop_amount(client=client)


async def check_account(account_data: str) -> bool:
    async with loader.semaphore:
        formatted_account: FormattedAccount | None = format_account(account_data=account_data)

        if not formatted_account:
            return False

        drop_value: float | None = await DropChecker(account_data=formatted_account).check_account()

        if not drop_value:
            logger.error(f'{formatted_account.address} | Not Eligible')
            return False

        account_data_dict: dict = {
            'address': formatted_account.address,
            'private_key': formatted_account.private_key,
            'mnemonic': formatted_account.mnemonic
        }
        account_data_for_file: str = ' | '.join([current_value for current_value
                                                 in account_data_dict.values()
                                                 if current_value])

        async with asyncio.Lock():
            async with aiofiles.open(file='eligible.txt',
                                     mode='a',
                                     encoding='utf-8-sig') as file:
                await file.write(f'{account_data_for_file} | {drop_value}\n')

        logger.success(f'{formatted_account.address} | Eliginle: {drop_value}')
