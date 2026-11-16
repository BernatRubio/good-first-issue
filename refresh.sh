#!/bin/bash
for lang in Python C++ Java Shell Typescript Rust; do
    uv run good-first-issue -l "$lang" -m 1000
done
