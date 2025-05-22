#!/bin/python3
'''
Web app to offer a frontend to the doc2oas tools

'''

import os
import shutil
import tempfile
import logging
import traceback
import sys
sys.dont_write_bytecode = True
from zipfile import ZipFile

from flask import Flask, flash, request, redirect, send_file, render_template, g
from werkzeug.utils import secure_filename
import docx
from markupsafe import Markup
import config
import main as doc2oas

class ReverseProxied(object):

    def __init__(self, the_app, script_name=None, scheme=None, server=None):
        self.app = the_app
        self.script_name = script_name
        self.scheme = scheme
        self.server = server

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '') or self.script_name
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
        scheme = environ.get('HTTP_X_SCHEME', '') or self.scheme
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        server = environ.get('HTTP_X_FORWARDED_HOST', '') or self.server
        if server:
            environ['HTTP_HOST'] = server
        return self.app(environ, start_response)


app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app, script_name='/doc2oas-ie')

UPLOAD_FOLDER = '/app/upload'

ALLOWED_EXTENSIONS = set(['txt', 'yaml', 'docx'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = config.SECRET
app.config['SESSION_TYPE'] = 'filesystem'

def allowed_file(filename):
    '''
    Check filename is in the list of allowed extensions
    '''
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def hello():
    '''
    Render home page
    '''
    if config.LAST_COMMIT is not False:
        link = config.REPO_URL+config.LAST_COMMIT.split(" ")[0]
    else:
        link = "#"

    return render_template(
        "./home.html",
        VERSION=config.VERSION,
        last_rev=config.LAST_COMMIT,
        rev_link=link
    )


@app.route("/doc2oas-info")
def doc2oas_info():
    '''
    Render home page
    '''
    return render_template("./doc2oas-details.html", VERSION=config.VERSION)


def get_all_yaml_file_paths_and_logs(directory):
    '''
    Finds yaml files within a directory and sub directories and
    returns the list of paths
    '''

    file_paths = []

    for root, _, files in os.walk(directory):
        for filename in files:
            logging.debug(filename)
            logging.debug(root)
            if ".yaml" in filename or ".log" in filename:
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)

    return file_paths


@app.after_request
def after_request(response):
    '''
    Clean up files created by doc2tosca
    '''
    if request.path != '/doc2oas':
        return response
    if g.get('tmp_dir') is None:
        return response

    for file_name in os.listdir('/app/upload'):
        # construct full file path
        file = '/app/upload/' + file_name
        if os.path.isfile(file):
            os.remove(file)
    
    shutil.rmtree(g.tmp_dir, ignore_errors=True)
    return response


@app.route("/doc2oas", methods=['POST'])
def mk_doc2oas():
    '''
    Executes doc2oas on the uploaded file
    '''

    tmp_dir="/app/tmp"
    os.makedirs(tmp_dir,exist_ok=True)
    logfilename = os.path.join(tmp_dir, 'doc2oastools.log')
    logging.basicConfig(filename=logfilename, force=True, level=logging.DEBUG)

    logging.info("Starting")
    logging.debug("TMP DIR: " + tmp_dir)

    zip_fn = "oas_defs.zip"
    zip_path = os.path.join(tmp_dir, zip_fn)

    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect("/doc2oas-ie")
    if 'configfile' not in request.files:
        flash('No config file uploaded')
        return redirect("/doc2oas-ie")

    ufiles = request.files.getlist("file")
    logging.debug("Number of files: " + str(len(ufiles)))
    uconfigfiles = request.files.getlist("configfile")
    logging.debug("Number of config files: " + str(len(uconfigfiles)))

    try:
        logging.debug(request.form)
    except:
        flash("Something went wrong :/")
        return redirect("/doc2oas-ie")

    docx_file = ufiles[0]
    config_file = uconfigfiles[0]
    oas_version = doc2oas.OAS_DICT["openapi"]

    filename_docx = secure_filename(docx_file.filename)
    filepath_docx = os.path.join(app.config['UPLOAD_FOLDER'], filename_docx)
    docx_file.save(filepath_docx)
    docx_file.close()
    filename_config = secure_filename(config_file.filename)
    filepath_config = os.path.join(app.config['UPLOAD_FOLDER'], filename_config)
    config_file.save(filepath_config)
    config_file.close()
    logging.debug("Starting conversion...")
    logging.debug(filepath_docx)
    logging.debug(filepath_config)
    try:
        doc2oas.maindoc2oas(
            filepath_docx, filepath_config
        )
    except ValueError as e:
        flash(str(e))
        return redirect("/doc2oas-ie")
    except BaseException as e:
        print(e)
        # logging.error(traceback.print_exc())
        flash(str(e))
        flash("Unknown error in the generation of the files. \
               Please contact the support.")
    finally:
        file_paths = get_all_yaml_file_paths_and_logs(tmp_dir)
        logging.debug(file_paths)
        with ZipFile(zip_path, 'w') as archive:
            for myfile in file_paths:
                logging.info(myfile)
                archive.write(myfile, arcname=os.path.basename(myfile))

        g.tmp_dir = tmp_dir
        return send_file(zip_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
