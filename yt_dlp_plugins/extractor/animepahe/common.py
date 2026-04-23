import itertools
import re
from collections.abc import Iterator

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import (
    ExtractorError,
    ISO639Utils,
    decode_packed_codes,
    get_domain,
    parse_duration,
    str_to_int,
)


class AnimepaheBaseIE(InfoExtractor):
    _VALID_URL = False
    PAHE_BASE_URL_RE = r'https://animepahe\.(?:si|com|pw|org)%s'
    TLD = ('si', 'com', 'pw', 'org')
    _DATA_RE = re.compile(r"""(?x)
                    data-src="(?P<url>https://kwik\.cx[^"]+)"[^>]+
                    data-resolution="(?P<height>\d+)"[^>]+
                    data-audio="(?P<lang>\w+)"
                    """)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._base_url = None

    def _real_initialize(self) -> None:
        from secrets import token_hex

        fake_ddg = token_hex(16)
        for s in self.TLD:
            self._set_cookie(f'.animepahe.{s}', '__ddg2_', fake_ddg)

    @staticmethod
    def title(title: str) -> str:
        clean = re.sub(r'animepahe|[\.:\',!]', '', title)
        return re.sub(r'\s+', ' ', clean).strip()

    @staticmethod
    def series(title: str) -> str:
        return re.sub(r'(?i)ep\s*\d+', '', title).strip()

    def episode_num(self, title: str) -> int | None:
        ep_num = self._search_regex(r'(?i)ep\s*(\d+)', title, 'episode num', fatal=False)
        return str_to_int(ep_num)

    def _get_base_url(self) -> str:
        if self._base_url is not None:
            return self._base_url

        for s in self.TLD:
            api_url = f'https://animepahe.{s}'
            resp = self._is_valid_url(api_url, s, item=api_url)
            if resp is False:
                continue
            self._base_url = api_url
            return self._base_url

    def _yield_formats(self, content: str) -> Iterator[dict[str, str | int | dict[str, str]]]:
        for data in self._DATA_RE.finditer(content):
            lang = data.group('lang')
            height = data.group('height')
            yield {
                'url': self._get_m3u8_url(data.group('url')),
                'height': str_to_int(height),
                'language': ISO639Utils.long2short(lang),
                'format_id': f'{height}-{lang}',
                'ext': 'mp4',
                'http_headers': {'referer': 'https://kwik.cx/'},
            }

    def _get_m3u8_url(self, url: str) -> str:
        encoded_page = self._download_webpage(url, self._generic_id(url), note='Downloading encoded page')
        decoded_page = decode_packed_codes(encoded_page)
        pattern = r'const\s*source\s*=\\\'(?P<url>[^\\]+)\\'
        return self._search_regex(pattern, decoded_page, name='m3u8 url', group='url')

    def _yield_entries(
        self, playlist_url: str, playlist_id: str, playlist_title: str, ie: str | object
    ) -> Iterator[dict[str, str | int | float]]:
        base_url = playlist_url.replace('/anime/', '/play/')
        for anime in self._fetch_page_entries(playlist_url, playlist_id):
            episode_num = str_to_int(anime.get('episode'))
            yield self.url_result(
                url_transparent=True,
                url=f'{base_url}/{anime.get("session")}',
                ie=ie,
                video_id=anime.get('id'),
                video_title=f'{playlist_title} Episode {episode_num}',
                episode_number=episode_num,
                duration=parse_duration(anime.get('duration')),
                thumbnail=anime.get('snapshot'),
                language=ISO639Utils.long2short(anime.get('audio')),
                series=playlist_title,
            )

    def _fetch_page_entries(self, url: str, playlist_id: str) -> Iterator[dict[str, str | int]]:
        api_url = f'https://{get_domain(url)}/api'
        for page_num in itertools.count(1):
            json_data = self._download_json(
                api_url,
                video_id=playlist_id,
                query={'m': 'release', 'id': playlist_id, 'sort': 'episode_asc', 'page': page_num},
                note=f'Downloading page {page_num}',
            )

            yield from self._yield_json(json_data)

            # End pagination if no next page is found.
            if not json_data.get('next_page_url'):
                break

    @staticmethod
    def _yield_json(j: dict) -> Iterator[dict[str, str | int]]:
        if not isinstance(j, dict) or not j:
            raise ExtractorError('Invalid JSON response: expected dict', expected=True)

        # Ensure data is a list before yielding.
        if isinstance(data := j.get('data'), list):
            yield from data
