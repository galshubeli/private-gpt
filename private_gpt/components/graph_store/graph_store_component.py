import logging
import typing

from injector import inject, singleton
from llama_index.core.graph_stores.types import (
    GraphStore,
)
from llama_index.core.indices.knowledge_graph import (
    KnowledgeGraphRAGRetriever,
)
from llama_index.core.llms.llm import LLM
from llama_index.core.storage import StorageContext

from private_gpt.settings.settings import Settings

logger = logging.getLogger(__name__)


@singleton
class GraphStoreComponent:
    settings: Settings
    graph_store: GraphStore | None = None

    @inject
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # If no graphstore is defined, return, making the graphstore optional
        if settings.graphstore is None:
            return

        match settings.graphstore.database:
            case "neo4j":
                try:
                    from llama_index.graph_stores.neo4j import (  # type: ignore
                        Neo4jGraphStore,
                    )
                except ImportError as e:
                    raise ImportError(
                        "Neo4j dependencies not found, install with `poetry install --extras graph-stores-neo4j`"
                    ) from e

                if settings.neo4j is None:
                    raise ValueError(
                        "Neo4j settings not found. Please provide settings."
                    )

                self.graph_store = typing.cast(
                    GraphStore,
                    Neo4jGraphStore(
                        **settings.neo4j.model_dump(exclude_none=True),
                    ),  # TODO
                )
            case "falkordb":
                try:
                    from llama_index.graph_stores.falkordb import (  # type: ignore
                        FalkorDBGraphStore,
                    )
                except ImportError as e:
                    raise ImportError(
                        "FalkorDB dependencies not found, install with `poetry install --extras graph-stores-falkordb`"
                    ) from e

                if settings.falkordb is None:
                    raise ValueError(
                        "FalkorDB settings not found. Please provide settings."
                    )

                self.graph_store = typing.cast(
                    FalkorDBGraphStore(
                        **settings.falkordb.model_dump(exclude_none=True),
                        decode_responses=True
                    ),  # TODO
                )
            case _:
                # Should be unreachable
                # The settings validator should have caught this
                raise ValueError(
                    f"Vectorstore database {settings.vectorstore.database} not supported"
                )

    def get_knowledge_graph(
        self,
        storage_context: StorageContext,
        llm: LLM,
    ) -> KnowledgeGraphRAGRetriever:
        if self.graph_store is None:
            raise ValueError("GraphStore not defined in settings")

        return KnowledgeGraphRAGRetriever(
            storage_context=storage_context,
            llm=llm,
            verbose=True,
        )

    def close(self) -> None:
        if self.graph_store and hasattr(self.graph_store.client, "close"):
            self.graph_store.client.close()
