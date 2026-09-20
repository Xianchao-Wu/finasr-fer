#########################################################################
# File Name: runvllm.sh
# Author: Xianchao Wu
# mail: xianchaow@nvidia.com
# Created Time: Wed 16 Sep 2026 09:59:07 AM UTC
#########################################################################
#!/bin/bash

bash scripts/start_qwen3_vllm.sh >> log.run.vllm 2>&1 & 
