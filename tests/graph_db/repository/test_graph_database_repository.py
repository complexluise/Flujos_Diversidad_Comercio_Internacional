import pytest
from unittest.mock import Mock, patch

# `graph_db` es un subsistema inconcluso (`upload_trade_data` es `pass`) y estos
# tests dependen de py2neo, que está descontinuado y no es dependencia del
# paquete. Se saltan en vez de romper CI, hasta decidir si el subsistema se
# retoma o se archiva. Ver docs/EVALUACION.md, sección 5.
py2neo = pytest.importorskip("py2neo", reason="py2neo no es dependencia del paquete")
Graph, Node, Relationship = py2neo.Graph, py2neo.Node, py2neo.Relationship

from graph_db.repository.graph_database_repository import GraphDatabaseRepository


@pytest.fixture
def mock_graph():
    with patch("py2neo.Graph") as mock:
        yield mock()


@pytest.fixture
def repo(mock_graph):
    return GraphDatabaseRepository(
        uri="bolt://localhost:7687", user="neo4j", password="test"
    )


def test_add_country(repo, mock_graph):
    # Test adding a country
    repo.add_country("USA", "United States of America")
    assert mock_graph.merge.called
    called_with_node = mock_graph.merge.call_args[0][0]
    assert isinstance(called_with_node, Node)
    assert called_with_node["iso3"] == "USA"
    assert called_with_node["name"] == "United States of America"
    assert called_with_node.labels == {"Country"}


def test_add_trade_relation(repo, mock_graph):
    # Test adding a trade relation
    repo.add_trade_relation("USA", "CAN", "Electronics", 2021, 500000, 400)
    assert mock_graph.merge.called
    called_with_rel = mock_graph.merge.call_args[0][0]
    assert isinstance(called_with_rel, Relationship)
    assert called_with_rel.type == "EXPORTS_TO"
    assert called_with_rel.start_node["iso3"] == "USA"
    assert called_with_rel.end_node["iso3"] == "CAN"
    assert called_with_rel["product_category"] == "Electronics"
    assert called_with_rel["year"] == 2021
    assert called_with_rel["value"] == 500000
    assert called_with_rel["quantity"] == 400


def test_find_trades(repo, mock_graph):
    # Prepare return value for the graph run method
    mock_graph.run.return_value = Mock(
        data=Mock(
            return_value=[
                {
                    "partner": "CAN",
                    "trades": [{"year": 2021, "value": 500000, "quantity": 400}],
                }
            ]
        )
    )

    # Test finding trades
    result = repo.find_trades("USA")
    assert result == [
        {"partner": "CAN", "trades": [{"year": 2021, "value": 500000, "quantity": 400}]}
    ]
    mock_graph.run.assert_called_once()
    query, params = mock_graph.run.call_args[0]
    assert "USA" in query
    assert params == {"iso3": "USA"}
