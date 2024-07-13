#!/bin/bash

source environment.env
export PYTHONPATH=/home/bea/choregraphe/lib/python2.7/site-packages
python2 nao_sound_processing.py --ip 192.168.1.101
