#!/bin/sh
# apply_patch.sh <patch_content>
echo "$1" | git apply -
