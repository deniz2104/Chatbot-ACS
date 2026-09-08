from src.spider.content_utils import normalize

class RomanianTokenizer:
    _stemmer = None

    @classmethod
    def _get_stemmer(cls):
        if cls._stemmer is None:
            import Stemmer
            cls._stemmer = Stemmer.Stemmer("romanian")
        return cls._stemmer

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        words = normalize(text).split()
        return cls._get_stemmer().stemWords(words)