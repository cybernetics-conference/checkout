#!/bin/bash

sudo echo "# Generated by resolvconf
nameserver 8.8.8.8
nameserver 8.8.4.4" > /etc/resolv.conf

echo "Should work! Try pinging a url."
