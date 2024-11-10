from flask import Flask, flash, redirect, render_template, request, session, abort,Blueprint, url_for
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, DataError
uri='postgresql://wf2322:St278-Ahobo$#cGHh@w4111.cisxo09blonu.us-east-1.rds.amazonaws.com/w4111'
engine=create_engine(uri)
