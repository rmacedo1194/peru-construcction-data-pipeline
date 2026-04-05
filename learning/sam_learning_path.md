# SAM Learning Path

Use these notes in this order.

## 1. First understand the local run itself

If you want to know what each local command means and why we use SAM instead of `uv run`, start here:

- [`sam_local_run_command_breakdown.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/sam_local_run_command_breakdown.md)

Then read the design choices behind that workflow:

- [`sam_local_run_decisions.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/sam_local_run_decisions.md)

## 2. Then understand AWS SAM itself

Read this next to understand what SAM is, what `sam build`, `sam local invoke`, and `sam deploy` do, and how local and cloud flows are connected:

- [`how_aws_sam_works.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/how_aws_sam_works.md)

## 3. Then understand discovery vs ingestion inputs

If you are confused about where dataset IDs and event payload values come from, read this next:

- [`dataset_selection_and_event_inputs.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/dataset_selection_and_event_inputs.md)

## 4. Then understand the Lambda code

This note explains the Lambda ingestion architecture itself:

- [`lambda_ingestion_architecture_notes.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/lambda_ingestion_architecture_notes.md)

If you want a more code-oriented walkthrough after that, read:

- [`lambda_app_code_walkthrough.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/lambda_app_code_walkthrough.md)

## 5. Then read the deployment view

Read this last to understand the architect and DevOps view of what you need before this part can run correctly in AWS:

- [`raw_ingestion_cloud_deployment_requirements.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/raw_ingestion_cloud_deployment_requirements.md)
- [`github_actions_deploy_dev_workflow.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/github_actions_deploy_dev_workflow.md)
