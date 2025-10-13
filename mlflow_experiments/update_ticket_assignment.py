import mlflow

from generate_onnx_model import create_and_log_onnx_model

def update_ticket_assignment_model():
    mlflow.set_experiment("MockShop Test Experiment")
    run_id_a_1 = create_and_log_onnx_model(
        "ticket_assignment",
        "",
        input_shape=(170, 9),
    )
    print(f"\nModel 'ticket_assignment' version logged from run {run_id_a_1}.")

if __name__ == "__main__":
    print("Starting ONNX model generation and registration script...")
    
    update_ticket_assignment_model()

    print("\nScript finished. Check the MLflow UI at http://localhost:5000 to see your runs and registered models.")