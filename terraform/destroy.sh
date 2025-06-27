#!/bin/bash

echo "Destroying AWS infrastructure..."

# Run terraform destroy with auto-approve
terraform destroy -auto-approve

echo "Destroy completed!" 