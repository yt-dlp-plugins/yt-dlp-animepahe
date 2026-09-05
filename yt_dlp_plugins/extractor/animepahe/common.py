import itertools
import re
from collections.abc import Iterator
from typing import Any

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import (
    ExtractorError,
    ISO639Utils,
    decode_packed_codes,
    get_element_by_class,
    parse_duration,
    str_to_int,
)


class AnimepaheBaseIE(InfoExtractor):
    PAHE_BASE_URL_RE = r'https://animepahe\.(?:com|pw|org)%s'
    _DATA_RE = re.compile(
        r'data-(?:src|url)="(?P<url>[^"]+)"[^>]*?data-fansub="(?P<fnsub>[^"]+)"[^>]*?data-resolution="(?P<height>[^"]+)"[^>]*?data-audio="(?P<lang>[^"]+)"'
    )
    _HEADERS = {
        'referer': 'https://animepahe.pw/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:155.0) Gecko/20100101 Firefox/155.0',
    }

    """
    def _real_initialize(self) -> None:
        print(self._get_cookies('https://animepahe.pw/'))
        self._set_cookie(domain='animepahe.pw', name='cf_clearance', value='aji pisang')
    """

    @staticmethod
    def title(title: str) -> str:
        clean = re.sub(r'animepahe|[\.:\',!]', '', title)
        return re.sub(r'\s+', ' ', clean).strip()

    @staticmethod
    def series(title: str) -> str:
        return re.sub(r'(?i)ep\s*\d+', '', title).strip()

    @staticmethod
    def episode_num(title: str) -> int | None:
        match = re.search(r'(?i)ep\s*(?P<num>\d+)', title)
        return str_to_int(match.group('num')) if match else None

    @staticmethod
    def _get_thumbnail(page: str) -> str | None:
        for s in ('sequel', 'prequel'):
            src = get_element_by_class(f'{s} hidden-sm-down', page)
            if src:
                match = re.search(r'data-src="(?P<img>[^"]+)"', src)
                return match.group('img') if match else None
        return None

    def _download_webpage(self, *args: Any, **kwargs: Any) -> str:
        return super()._download_webpage(*args, **kwargs, headers=self._HEADERS, impersonate=True)

    def _yield_formats(self, content: str) -> Iterator[dict[str, str | int | dict[str, str] | None]]:
        lang_pref = self._configuration_arg(key='lang', default='all')
        skipped_langs = set()
        for data in self._DATA_RE.finditer(content):
            self.write_debug(f'data from _yield_formats: {data}')
            lang_code = ISO639Utils.long2short(lang := data.group('lang'))
            self.write_debug(f'lang code: {lang_code}')
            if 'all' not in lang_pref and lang_code not in lang_pref:
                if lang_code not in skipped_langs:
                    self.write_debug(f'Skipping {lang_code!r}: not in preferred languages {lang_pref!r}')
                    skipped_langs.add(lang_code)
                continue
            if not (url := self._get_m3u8_url(data.group('url'))):
                continue

            yield {
                'url': url,
                'height': str_to_int(height := data.group('height')),
                'language': lang_code,
                'format_id': f'{height}-{lang}',
                'format_note': data.group('fnsub'),
                'ext': 'mp4',
                'http_headers': {'referer': 'https://kwik.cx/'},
            }

    def _get_m3u8_url(self, url: str) -> str | None:
        fatal = not self.get_param('ignore_no_formats_error')
        if not (
            encoded_page := self._download_webpage(
                url,
                self._generic_id(url),
                note='Downloading encoded page',
                fatal=fatal,
            )
        ):
            return None
        decoded_page = decode_packed_codes(encoded_page)
        return self._search_regex(r'const\s*source\s*=\\\'([^\\]+)\\', decoded_page, name='m3u8 url', fatal=fatal)

    def _yield_entries(
        self, playlist_url: str, playlist_id: str, playlist_title: str
    ) -> Iterator[dict[str, str | None | float]]:
        base_url = playlist_url.replace('/anime/', '/play/')
        for anime in self._fetch_page_entries(playlist_url, playlist_id):
            episode_num = str_to_int(anime.get('episode'))
            yield self.url_result(
                url_transparent=True,
                url=f'{base_url}/{anime.get("session")}',
                ie='Animepahe',
                video_id=anime.get('id'),
                video_title=f'{playlist_title} Episode {episode_num}',
                episode_number=episode_num,
                duration=parse_duration(anime.get('duration')),
                thumbnail=anime.get('snapshot'),
                language=ISO639Utils.long2short(anime.get('audio')),
                series=playlist_title,
            )

    def _fetch_page_entries(self, url: str, playlist_id: str) -> Iterator[dict[str, str | int]]:
        for page_num in itertools.count(1):
            result = self._download_json(
                url_or_request='https://animepahe.pw/api',
                video_id=playlist_id,
                query={'m': 'release', 'id': playlist_id, 'sort': 'episode_asc', 'page': str(page_num)},
                note=f'Downloading page {page_num}',
                headers=self._HEADERS,
                impersonate=True,
            )

            yield from self._yield_json(result)

            # End pagination if no next page is found.
            if not result.get('next_page_url'):
                break

    @staticmethod
    def _yield_json(j: dict) -> Iterator[dict[str, str | int]]:
        if not isinstance(j, dict) or not j:
            raise ExtractorError('Invalid JSON response: expected dict', expected=True)

        # Ensure data is a list before yielding.
        if isinstance(data := j.get('data'), list):
            yield from data


# vim: ft=python:nowrap
