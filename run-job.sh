#!/bin/bash
# run-job.sh - Run a one-shot harness task as a K8s Job

if [ -z "$1" ]; then
    echo "Usage: ./run-job.sh \"your task here\""
    exit 1
fi

TASK="$1"
JOB_NAME="harness-task-$(date +%s)-$RANDOM"

# Substitute task into template and apply
export TASK
export JOB_ID="$JOB_NAME"
envsubst '${TASK} ${JOB_ID}' < k8s/jobs/agent-job-template.yml | \
    sed "s/generateName: harness-task-/name: $JOB_NAME/" | \
    kubectl apply -f - > /dev/null

echo "Running: $TASK"
echo "---"

# Wait for pod to be created, then stream logs
sleep 2
kubectl -n harness logs -f job/$JOB_NAME 2>/dev/null

# Wait for job completion and get exit code
kubectl -n harness wait --for=condition=complete job/$JOB_NAME --timeout=300s > /dev/null 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    kubectl -n harness wait --for=condition=failed job/$JOB_NAME --timeout=5s > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "---"
        echo "Job failed."
        exit 1
    fi
fi