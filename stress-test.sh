#/bin/bash

# get the instance ids in order to ssh and run stress tests
az vmss list-instance-connection-info \
  --resource-group acdnd-c4-project \
  --name udacity-vmss