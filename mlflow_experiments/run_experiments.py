import mlflow

from generate_onnx_model import create_and_log_onnx_model
from update_ticket_assignment import update_ticket_assignment_model

EXPERIMENT_NAME = "MockShop Test Experiment"

if __name__ == "__main__":
    print("Starting ONNX model generation and registration script...")

    if(mlflow.get_experiment_by_name(EXPERIMENT_NAME) is not None):
      update_ticket_assignment_model()
      exit(0)

    mlflow.set_experiment(EXPERIMENT_NAME)

    run_id_a_1 = create_and_log_onnx_model(
        "ticket_assignment",
        "",
        input_shape=(100, 5),
    )
    print(f"\nModel 'ticket_assignment' version logged from run {run_id_a_1}.")
    
    
    run_id_a_2 = create_and_log_onnx_model(
        "ticket_assignment",
        "",
        input_shape=(150, 7)
    )
    print(f"\nModel 'ticket_assignment' version logged from run {run_id_a_2}.")


    run_id_b_1 = create_and_log_onnx_model(
        "sale_prediction",
        "",
        input_shape=(100, 5),
    )
    print(f"\nModel 'sale_prediction' version logged from run {run_id_b_1}.")


    run_id_b_2 = create_and_log_onnx_model(
        "sale_prediction",
        "",
        input_shape=(150, 7),
        alias="stable"
    )
    print(f"\nModel 'sale_prediction' version logged from run {run_id_b_2}.")
    
    
    run_id_b_3 = create_and_log_onnx_model(
        "sale_prediction",
        "",
        input_shape=(170, 9),
        alias="experimental"
    )
    print(f"\nModel 'sale_prediction' version logged from run {run_id_b_3}.")
    
    
    run_id_c_1 = create_and_log_onnx_model(
        "product_recommendation",
        "",
        input_shape=(100, 5),
    )
    print(f"\nModel 'product_recommendation' version logged from run {run_id_c_1}.")

    
    run_id_c_2 = create_and_log_onnx_model(
        "product_recommendation",
        "",
        input_shape=(150, 7),
        tags={"stage": "production"},
    )
    print(f"\nModel 'product_recommendation' version logged from run {run_id_c_2}.")

    run_id_c_3 = create_and_log_onnx_model(
        "product_recommendation",
        "",
        input_shape=(170, 9),
        tags={"stage": "production"},
    )
    print(f"\nModel 'product_recommendation' version logged from run {run_id_c_3}.")

    print("\nScript finished. Check the MLflow UI at http://localhost:5000 to see your runs and registered models.")