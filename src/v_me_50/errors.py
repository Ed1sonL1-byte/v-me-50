"""Domain failures; API and command-line callers decide how to present them."""

from .models import Movie


class RAGError(Exception):
    pass


class ConfigurationError(RAGError):
    pass


class ModelUnavailable(RAGError):
    pass


class InvalidModelOutput(RAGError):
    pass


class RepositoryUnavailable(RAGError):
    pass


class InvalidRequest(ValueError):
    pass


class UnknownReference(ValueError):
    pass


class AmbiguousReference(ValueError):
    def __init__(self, title: str, matches: list[Movie]):
        self.title = title
        self.matches = matches
        super().__init__(f"Multiple movies match '{title}'; add a release year.")
