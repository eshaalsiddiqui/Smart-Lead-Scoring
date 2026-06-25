"""
MLflow Configuration for Smart Lead Scoring CRM
Handles experiment tracking, model registry, and deployment
"""

import logging
import os
from pathlib import Path

import mlflow
import mlflow.lightgbm
import mlflow.sklearn
import mlflow.xgboost
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)


class MLflowManager:
    def __init__(self, tracking_uri: str = None, experiment_name: str = "lead_scoring"):
        """
        Initialize MLflow manager

        Args:
            tracking_uri: MLflow tracking server URI
            experiment_name: Name of the experiment
        """
        self.tracking_uri = tracking_uri or os.getenv(
            "MLFLOW_TRACKING_URI", "http://localhost:5000"
        )
        self.experiment_name = experiment_name
        self.client = None

        self._setup_mlflow()

    def _setup_mlflow(self):
        """Setup MLflow tracking"""
        try:
            mlflow.set_tracking_uri(self.tracking_uri)
            mlflow.set_experiment(self.experiment_name)

            # Initialize client
            self.client = MlflowClient(tracking_uri=self.tracking_uri)

            logger.info(f"MLflow tracking initialized: {self.tracking_uri}")
            logger.info(f"Experiment: {self.experiment_name}")

        except Exception as e:
            logger.error(f"Failed to initialize MLflow: {str(e)}")
            raise

    def log_model_performance(
        self,
        run_id: str,
        model_name: str,
        metrics: dict,
        params: dict = None,
        tags: dict = None,
    ):
        """
        Log model performance metrics

        Args:
            run_id: MLflow run ID
            model_name: Name of the model
            metrics: Dictionary of metrics to log
            params: Dictionary of parameters to log
            tags: Dictionary of tags to log
        """
        try:
            with mlflow.start_run(run_id=run_id):
                # Log metrics
                for metric_name, metric_value in metrics.items():
                    mlflow.log_metric(metric_name, metric_value)

                # Log parameters
                if params:
                    for param_name, param_value in params.items():
                        mlflow.log_param(param_name, param_value)

                # Log tags
                if tags:
                    for tag_name, tag_value in tags.items():
                        mlflow.set_tag(tag_name, tag_value)

                logger.info(f"Logged performance for {model_name}")

        except Exception as e:
            logger.error(f"Failed to log model performance: {str(e)}")
            raise

    def register_model(
        self,
        run_id: str,
        model_path: str,
        model_name: str,
        description: str = None,
        tags: dict = None,
    ):
        """
        Register model in MLflow Model Registry

        Args:
            run_id: MLflow run ID
            model_path: Path to the model file
            model_name: Name for the registered model
            description: Description of the model
            tags: Tags for the model
        """
        try:
            # Register model
            model_version = mlflow.register_model(
                f"runs:/{run_id}/{model_path}", model_name
            )

            # Add description
            if description:
                self.client.update_model_version(
                    name=model_name,
                    version=model_version.version,
                    description=description,
                )

            # Add tags
            if tags:
                for tag_name, tag_value in tags.items():
                    self.client.set_model_version_tag(
                        name=model_name,
                        version=model_version.version,
                        key=tag_name,
                        value=tag_value,
                    )

            logger.info(
                f"Registered model {model_name} version {model_version.version}"
            )
            return model_version

        except Exception as e:
            logger.error(f"Failed to register model: {str(e)}")
            raise

    def promote_model_to_staging(self, model_name: str, version: str = None):
        """
        Promote model to staging

        Args:
            model_name: Name of the model
            version: Version to promote (latest if None)
        """
        try:
            if not version:
                # Get latest version
                latest_version = self.client.get_latest_versions(model_name)[0]
                version = latest_version.version

            # Transition to Staging
            self.client.transition_model_version_stage(
                name=model_name, version=version, stage="Staging"
            )

            logger.info(f"Promoted {model_name} version {version} to Staging")

        except Exception as e:
            logger.error(f"Failed to promote model to staging: {str(e)}")
            raise

    def promote_model_to_production(self, model_name: str, version: str = None):
        """
        Promote model to production

        Args:
            model_name: Name of the model
            version: Version to promote (latest if None)
        """
        try:
            if not version:
                # Get latest staging version
                staging_versions = self.client.get_latest_versions(
                    model_name, stages=["Staging"]
                )
                if not staging_versions:
                    raise ValueError("No staging version found")
                version = staging_versions[0].version

            # Transition to Production
            self.client.transition_model_version_stage(
                name=model_name, version=version, stage="Production"
            )

            logger.info(f"Promoted {model_name} version {version} to Production")

        except Exception as e:
            logger.error(f"Failed to promote model to production: {str(e)}")
            raise

    def get_production_model(self, model_name: str):
        """
        Get production model

        Args:
            model_name: Name of the model

        Returns:
            Model version info
        """
        try:
            production_versions = self.client.get_latest_versions(
                model_name, stages=["Production"]
            )

            if not production_versions:
                raise ValueError(f"No production version found for {model_name}")

            return production_versions[0]

        except Exception as e:
            logger.error(f"Failed to get production model: {str(e)}")
            raise

    def compare_models(
        self, model_name: str, metric_name: str = "auc_score", limit: int = 10
    ):
        """
        Compare model versions

        Args:
            model_name: Name of the model
            metric_name: Metric to compare
            limit: Number of versions to compare

        Returns:
            List of model versions sorted by metric
        """
        try:
            # Get all versions
            versions = self.client.search_model_versions(f"name='{model_name}'")

            # Get runs for each version
            model_runs = []
            for version in versions[:limit]:
                run = self.client.get_run(version.run_id)
                metrics = run.data.metrics

                if metric_name in metrics:
                    model_runs.append(
                        {
                            "version": version.version,
                            "stage": version.current_stage,
                            "metric_value": metrics[metric_name],
                            "run_id": version.run_id,
                            "creation_timestamp": version.creation_timestamp,
                        }
                    )

            # Sort by metric value
            model_runs.sort(key=lambda x: x["metric_value"], reverse=True)

            return model_runs

        except Exception as e:
            logger.error(f"Failed to compare models: {str(e)}")
            raise

    def get_experiment_runs(self, experiment_id: str = None, limit: int = 100):
        """
        Get experiment runs

        Args:
            experiment_id: Experiment ID (uses current if None)
            limit: Number of runs to return

        Returns:
            List of runs
        """
        try:
            if not experiment_id:
                experiment = mlflow.get_experiment_by_name(self.experiment_name)
                experiment_id = experiment.experiment_id

            runs = self.client.search_runs(
                experiment_ids=[experiment_id],
                run_view_type=ViewType.ALL,
                max_results=limit,
            )

            return runs

        except Exception as e:
            logger.error(f"Failed to get experiment runs: {str(e)}")
            raise

    def create_model_deployment(
        self, model_name: str, version: str = None, deployment_name: str = None
    ):
        """
        Create model deployment (for MLflow deployment)

        Args:
            model_name: Name of the model
            version: Version to deploy (latest production if None)
            deployment_name: Name for the deployment

        Returns:
            Deployment info
        """
        try:
            if not version:
                production_model = self.get_production_model(model_name)
                version = production_model.version

            if not deployment_name:
                deployment_name = f"{model_name}-v{version}"

            # This would integrate with MLflow deployment tools
            # For now, return deployment info
            deployment_info = {
                "name": deployment_name,
                "model_name": model_name,
                "version": version,
                "status": "created",
            }

            logger.info(f"Created deployment {deployment_name}")
            return deployment_info

        except Exception as e:
            logger.error(f"Failed to create model deployment: {str(e)}")
            raise


# Global MLflow manager instance
mlflow_manager = MLflowManager()


def get_mlflow_manager():
    """Get global MLflow manager instance"""
    return mlflow_manager
