#!/usr/bin/python2.7
#coding: utf-8

from distutils.core import setup, Extension

MOD = "避免死锁"

setup(name = MOD, ext_modules = [Extension(MOD, sources = ['避免死锁.c', 'testc_wrapper.c'])])
