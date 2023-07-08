import re
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple, List, Callable, Type

from .meta import DocumentMeta
from ...core.domain.entity import AggregateRoot, Entity


@dataclass
class Document(AggregateRoot):
    """Present a markdown file into DomainObject."""

    file_id: str
    meta: DocumentMeta
    content: str | None

    # SQLAlchemy mapper args.
    __mapper_args__ = dict()

    # Overwrite.

    def __eq__(self, __o: object) -> bool:
        return __o.file_id == self.file_id if isinstance(__o, type(self)) else False

    def __hash__(self) -> int:
        return hash(self.file_id)

    @classmethod
    def load(cls, meta: DocumentMeta, content: str) -> "Document":
        return Document(file_id=meta.name, meta=meta, content=content)

    @classmethod
    def getmeta(cls, meta: DocumentMeta) -> "Document":
        return Document(file_id=meta.name, meta=meta, content="")


Section = Dict[str, Tuple[int | Tuple[int], str | Type["Section"] | Iterable[str | Type["Section"]]]]
"""{header name: (header level, content/sub paragraph)}"""


class ParsedDocumentBody(Entity):
    """"""

    id: str  # Query by MAIN title.
    """In ParsedDocumentBody, `id` refers `title`."""
    index: Iterable[str]  # except title.
    content: Iterable[Section]


Condition = bool | int | str | Enum
"""`Condition` musrt be same in condition_checker and producer."""


class ContentSplitService:
    """Generic content splitor interface."""

    header_split_pattern: re.Pattern
    getheaderbody: Callable[[str], str]
    """Get body of header.`('## Bla bla' => 'Bla bla')`"""
    getheaderlevel: Callable[[str], int]
    """Get header level.`('## Bla bla' => 2)`"""
    getmetadata: Callable[[str], Dict[str, Any]]
    pruningservice: Callable[[Iterable[str]], List[str] | None]
    poptitleservice: Callable[[str], Tuple[str, str | None]]

    def __init__(
        self,
        metadata_service: Callable[[str], Dict[str, Any]],
        header_split_pattern: re.Pattern,
        headerbody_parser: Callable[[str], str],
        headerlevel_parser: Callable[[str], int],
        pruning_condition: Callable[[Iterable[str]], Condition],
        pruning_service: Callable[[Iterable[str], Condition], List[str] | None],
        pop_title_service: Callable[[str], Tuple[str, str | None]],
    ) -> None:
        self.getmetadata = metadata_service
        self.header_split_pattern = header_split_pattern
        self.getheaderbody = headerbody_parser
        self.getheaderlevel = headerlevel_parser
        self.pruningservice = lambda content: pruning_service(
            content, pruning_condition(content)
        )
        self.poptitleservice = pop_title_service

    def parse(self, content: str) -> Tuple[DocumentMeta | None, ParsedDocumentBody] | None:
        content_chain = re.split(self.header_split_pattern, content)

        content, title = self.poptitleservice(content)

        metadata_in_file = self.getmetadata(content)
        
        title = title or metadata_in_file.get("title", None)

        _res = self.pruningservice(content_chain)
        if _res:
            content_chain = _res
        # Strcture of content_chain:
        # [
        # <header>, <content>,
        # <header>, <content>,
        # ...
        # <header>, [<content>]
        # ]

        paragraph_chain: List[Section] = []

        if paragraph_num := len(content_chain) % 2 == 0:
            # Last one in content.
            paragraph_num = int(paragraph_num / 2)
        else:
            # Last one is header.
            # Last MUST be <header: [...]>, <content: "">
            content_chain.append("")
            paragraph_num = int((paragraph_num + 1) / 2)

        # Build.
        for idx in range(paragraph_num):
            # header, content
            #   ||      ||
            #   2x,    2x+1(may out of index)
            paragraph_chain.append(
                {
                    self.getheaderbody(content_chain[idx * 2]): (
                        self.getheaderlevel(content_chain[idx * 2]),
                        content_chain[idx * 2 + 1],
                    )
                }
            )

        # Orgnize.
        section_chain: Iterable[Section] = []

        for section in paragraph_chain:
            ...
