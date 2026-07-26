from pathlib import Path

import pandas as pd

from .constants import BACIColumnsTradeData

DEFAULT_FILENAME_TEMPLATE = "cleaned_HS92_Y{year}_V202401b.csv"

# Columnas mínimas para que funcionen todos los análisis del paquete. `mass` es
# imprescindible: sin ella `compute_entity_trade_metrics` falla con KeyError.
DEFAULT_COLUMNS = (
    BACIColumnsTradeData.PRODUCT_CATEGORY_CODE.value,
    BACIColumnsTradeData.EXPORTER_ISO_CODE_3.value,
    BACIColumnsTradeData.IMPORTER_ISO_CODE_3.value,
    BACIColumnsTradeData.MONEY.value,
    BACIColumnsTradeData.MASS.value,
)


class TradeDataLoader:
    """
    Responsable de cargar y preprocesar los datos de comercio.
    """

    def __init__(
            self,
            data_dir: str,
            filename_template: str = DEFAULT_FILENAME_TEMPLATE,
    ):
        """
        Args:
            data_dir (str): Directorio donde están los CSV de comercio limpios.
            filename_template (str): Plantilla del nombre de archivo, con un
                campo `{year}`. Permite trabajar con otras versiones de BACI sin
                renombrar archivos.
        """
        self.data_dir = data_dir
        self.filename_template = filename_template

    def load_trade_data(
            self,
            year: int,
            columns: tuple[str, ...] | None = None,
    ) -> pd.DataFrame:
        """
        Carga los datos de comercio para el año especificado.

        Args:
            year (int): El año para el cual se deben cargar los datos.
            columns (tuple[str, ...] | None): Columnas a leer. Por defecto lee
                las necesarias para todos los análisis del paquete.

        Returns:
            pd.DataFrame: El DataFrame con los datos de comercio.

        Raises:
            FileNotFoundError: Si no existe el archivo del año pedido.
            ValueError: Si al archivo le faltan columnas requeridas.
        """
        file_path = Path(self.data_dir) / self.filename_template.format(year=year)
        if not file_path.exists():
            raise FileNotFoundError(
                f"No se encontró {file_path}. Verifica `data_dir` y que los datos "
                f"del año {year} estén limpios. Para probar la librería sin datos "
                f"reales usa `complex_trade_flow.samples.load_sample_network()`."
            )

        requested = tuple(columns) if columns is not None else DEFAULT_COLUMNS
        available = set(pd.read_csv(file_path, nrows=0).columns)
        missing = [column for column in requested if column not in available]
        if missing:
            raise ValueError(
                f"A {file_path} le faltan las columnas {missing}. "
                f"Columnas encontradas: {sorted(available)}."
            )

        return pd.read_csv(
            file_path,
            usecols=list(requested),
            low_memory=False,
        )
