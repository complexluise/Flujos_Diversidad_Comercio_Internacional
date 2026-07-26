from __future__ import annotations

import os

import pandas as pd

from collections.abc import Callable
from pandas import DataFrame
from tqdm import tqdm
from joblib import Parallel, delayed

from .constants import EconomicComplexity, BACIColumnsTradeData
from .diversity_metrics import DiversityCalculator
from .utils import ClassificationScheme
from .networks import TradeNetwork


class EconomicDiversityAnalyzer:
    """
    TODO: algunas cosas acopladas como los directorios
    """
    def __init__(
            self,
            start_year: int,
            end_year: int,
            classification_schemes: list[ClassificationScheme]
    ):
        self.start_year = start_year
        self.end_year = end_year
        self.classification_schemes = classification_schemes
        self.analysis_dict: dict[EconomicComplexity, Callable] = {
            EconomicComplexity.ENTITY_PRODUCT_DIVERSIFICATION.value: self.compute_entity_product_diversification,
            EconomicComplexity.ENTITY_TRADE_METRICS.value: self.compute_entity_trade_metrics
        }

    def analyze_year(
            self, year: int,
            scheme_name: str,
            type_analysis: EconomicComplexity,
            base_directory: str
    ) -> DataFrame:
        network = TradeNetwork.from_year(
            year,
            classification_schemes=self.classification_schemes,
            base_directory=base_directory
        )

        analysis: Callable = self.analysis_dict[type_analysis.value]

        results = Parallel(n_jobs=-1)(
            delayed(analysis)(network, entity, scheme_name) for entity in
            tqdm(network.entities[scheme_name], desc=f"Analyzing year {year}")
        )

        return pd.DataFrame(results)

    def run_analysis(
            self,
            type_analysis: EconomicComplexity,
            output_directory: str,
            base_directory: str,
    ) -> None:
        """
        Runs the diversity analysis for each year and classification scheme, and stores the results.
        """

        for scheme in self.classification_schemes:
            for year in range(self.start_year, self.end_year + 1):
                print(f"Analyzing {scheme.name} for {year}...")
                analysis_df = self.analyze_year(
                    year,
                    scheme.name,
                    type_analysis,
                    base_directory=base_directory,
                )
                self.save_csv(analysis_df, output_directory, scheme.name, year, type_analysis.value)

    @staticmethod
    def save_csv(df, output_directory, scheme_name, year, analysis):
        # TODO: esta función de guarado esta acoplada a la diversidad
        output_path = os.path.join(output_directory, analysis)
        os.makedirs(output_path, exist_ok=True)
        output_filename = f"{scheme_name}_{analysis}_{year}.csv"
        df.to_csv(os.path.join(output_path, output_filename), index=False)
        print(f"Saved results to {os.path.join(output_path, output_filename)}")

    @staticmethod
    def compute_entity_product_diversification(
            trade_network: TradeNetwork,
            entity: str,
            scheme_name: str
    ) -> dict:
        calculator = DiversityCalculator()
        return {
            scheme_name: entity,
            "export_product_diversity": calculator.calculate_diversity_index(
                data=trade_network.filter_data_by_entities(
                            scheme_name=scheme_name,
                            exporters=[entity]
                        )
            ),
            "import_product_diversity": calculator.calculate_diversity_index(
                data=trade_network.filter_data_by_entities(
                    scheme_name=scheme_name,
                    importers=[entity],
                )
            ),
        }


    @staticmethod
    def compute_entity_trade_metrics(
            trade_network: TradeNetwork,
            entity: str,
            scheme_name: str

    ) -> dict:
        """
        Calculates various trade metrics for a given entity:
        - Money gained through exports
        - Money lost through imports
        - Mass gained through imports
        - Mass lost through exports
        - Entropy metrics for imports and exports
        - Center/periphery level

        Args:
            trade_network: The trade network containing the trade data
            entity: The entity (country, region) to analyze
            scheme_name: The classification scheme name

        Returns:
            dict: A dictionary containing the calculated metrics
        """
        calculator = DiversityCalculator()

        export_data = trade_network.filter_data_by_entities(
            scheme_name=scheme_name,
            exporters=[entity]
        )

        import_data = trade_network.filter_data_by_entities(
            scheme_name=scheme_name,
            importers=[entity]
        )

        money_gain_exportation = export_data[BACIColumnsTradeData.MONEY.value].sum()
        money_loss_importation = import_data[BACIColumnsTradeData.MONEY.value].sum()

        return {
            scheme_name: entity,
            "MONEY_GAIN_EXPORTATION": money_gain_exportation,
            "MONEY_LOSS_IMPORTATION": money_loss_importation,
            "MASS_GAIN_IMPORTATION": import_data[BACIColumnsTradeData.MASS.value].sum(),
            "MASS_LOSS_EXPORTATION": export_data[BACIColumnsTradeData.MASS.value].sum(),
            "ENTROPY_MONEY_LOSS_EXPORTATION": calculator.calculate_diversity_index(
                data=trade_network.filter_data_by_entities(
                            scheme_name=scheme_name,
                            exporters=[entity]
                        )
            ),
            "ENTROPY_MONEY_GAIN_IMPORTATION": calculator.calculate_diversity_index(
                data=trade_network.filter_data_by_entities(
                    scheme_name=scheme_name,
                    importers=[entity],
                ),
            ),
            "ENTROPY_MASS_LOSS_EXPORTATION": calculator.calculate_diversity_index(
                data=trade_network.filter_data_by_entities(
                    scheme_name=scheme_name,
                    exporters=[entity],
                ),
                column="mass",
            ),
            "ENTROPY_MASS_GAIN_IMPORTATION": calculator.calculate_diversity_index(
                data=trade_network.filter_data_by_entities(
                    scheme_name=scheme_name,
                    importers=[entity],
                ),
                column="mass",
            ),
            # OJO: esto NO es una medida de centro-periferia, es solo el ratio
            # exportaciones/importaciones. El nombre se conserva por
            # compatibilidad. La implementación real de la metodología de
            # Cajas (2025) está en sandbox/centro_periferia_refactor.py y aún
            # no se ha integrado al paquete.
            "EXPORT_IMPORT_RATIO": (
                money_gain_exportation / money_loss_importation
                if money_loss_importation > 0 else float("inf")
            ),
        }
