
import mlflow
import mlflow.onnx
import mlflow.tracking
from sklearn.linear_model import LinearRegression
from sklearn.datasets import make_regression
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


def create_and_log_onnx_model(model_name, version_description, input_shape=(10, 3), alias: str = None, tags: dict = {}):
    """
    Trains a simple scikit-learn model, converts it to ONNX,
    logs it to MLflow, and registers it in the Model Registry.
    """
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"MLflow Run ID: {run_id}")

        # 1. Generate synthetic data
        X, y = make_regression(n_samples=input_shape[0], n_features=input_shape[1], random_state=42)
        
        # 2. Train a simple scikit-learn model
        model = LinearRegression()
        model.fit(X, y)

        print("Model trained.")

        # 3. Log parameters and metrics (optional)
        mlflow.log_param("n_samples", input_shape[0])
        mlflow.log_param("n_features", input_shape[1])

        # 4. Convert scikit-learn model to ONNX format
        initial_type = [('input', FloatTensorType([None, input_shape[1]]))]
        onnx_model = convert_sklearn(model, initial_types=initial_type)

        # 5. Log the ONNX model to MLflow
        model_info = mlflow.onnx.log_model(
            onnx_model=onnx_model,
            name=model_name,
            registered_model_name=model_name,
            signature=mlflow.models.infer_signature(X, y),
            input_example=X[:2],
            tags=tags,
        )
        print(f"ONNX model logged and registered as '{model_name}'.")
        print(f"Artifact path: {model_info.artifact_path}")

        # 6. Set a description for the registered model version
        client = mlflow.tracking.MlflowClient()
        try:
            latest_version = client.get_latest_versions(model_name)[0].version
            if alias:
                client.set_registered_model_alias(model_name, alias, latest_version)
            if tags:
              for key, value in tags.items():
                client.set_model_version_tag(model_name, version=latest_version, key=key, value=value)
            client.update_model_version(
                name=model_name,
                version=latest_version,
                description=version_description
            )
            print(f"Registered model '{model_name}' version {latest_version} description updated.")
        except Exception as e:
            print(f"Could not update model version description for {model_name}: {e}")
            print("This might happen if it's the very first registration and no version is immediately available.")

        return run_id