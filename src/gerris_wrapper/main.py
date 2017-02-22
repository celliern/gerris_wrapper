#!/usr/bin/env python
# coding=utf8

import logging
import subprocess
import multiprocessing as mp
import numpy as np
from io import StringIO

from path import Path, tempfile

logger = logging.getLogger(__name__)
logger.handlers = []
logger.addHandler(logging.NullHandler())

gerris_logger = logging.getLogger('.'.join([__name__, 'gerris_log']))
gerris_logger.handlers = []
gerris_logger.addHandler(logging.NullHandler())


def log_subprocess_output(pipe):
    for line in iter(pipe.readline, b''):  # b'\n'-separated lines
        gerris_logger.info(line.decode().strip('\n'))


def _assert_files(gfs_file, working_dir):
    """Ensure the files and directory are here and convert them as path.Path

    This function will coerce the string as a path.py Path and assert if
    mandatory files or directory are missing.
    """

    if gfs_file is not None:
        gfs_file = Path(gfs_file)
        logger.debug(f'looking for gfs file ({gfs_file.abspath()})')
        assert gfs_file.isfile(), "gfs file not found"

    working_dir = Path(working_dir)
    logger.debug(
        f'checking if working directory ({working_dir.abspath()}) exist')
    assert working_dir.isdir(), "Working directory does not exist"

    return gfs_file, working_dir


def run(gfs_file,
        output_file,
        working_dir="."):

    logger.info('check consistency of input files')
    gfs_file, working_dir, = _assert_files(gfs_file, working_dir)

    command = (['docker', 'run', '--rm',
                '-v', f'{gfs_file.abspath()}:/root/{gfs_file.basename()}',
                '-v', f'{working_dir.abspath()}:/root',
                'gerris', 'gerris2D', '-m',
                str(gfs_file.basename())])
    logger.debug('command line : %s' % ' '.join(command))

    logger.info('starting gerris simulation...')
    with open(output_file, 'wb') as f:
        with subprocess.Popen(command,
                              stdout=f,
                              stderr=subprocess.PIPE) as process:
            with process.stderr:
                log_subprocess_output(process.stderr)
            assert process.wait() == 0, 'sys call failed'
    logger.info('gerris simulation finished')


def split(gfs_file,
          output_file,
          split_number=2,
          working_dir="."):

    logger.info('check consistency of input files')
    gfs_file, working_dir, = _assert_files(gfs_file, working_dir)

    command = (['docker', 'run', '--rm',
                '-v', f'{gfs_file.abspath()}:/root/{gfs_file.basename()}',
                '-v', f'{working_dir.abspath()}:/root',
                'gerris', 'gerris2D', '-ms', str(split_number),
                str(gfs_file.basename())])
    logger.debug('command line : %s' % ' '.join(command))

    logger.info('split simulation file ...')
    with open(output_file, 'wb') as f:
        with subprocess.Popen(command,
                              stdout=f,
                              stderr=subprocess.PIPE) as process:
            with process.stderr:
                log_subprocess_output(process.stderr)
            assert process.wait() == 0, 'sys call failed'


def parallelize(gfs_file,
                output_file,
                n=mp.cpu_count(),
                working_dir="."):

    logger.info('check consistency of input files')
    gfs_file, working_dir, = _assert_files(gfs_file, working_dir)

    command = (['docker', 'run', '--rm',
                '-v', f'{gfs_file.abspath()}:/root/{gfs_file.basename()}',
                '-v', f'{working_dir.abspath()}:/root',
                'gerris', 'gerris2D', '-mb', str(n),
                str(gfs_file.basename())])

    logger.debug('command line : %s' % ' '.join(command))

    logger.info('parallelize simulation file ...')
    with open(output_file, 'wb') as f:
        with subprocess.Popen(command,
                              stdout=f,
                              stderr=subprocess.PIPE) as process:
            with process.stderr:
                log_subprocess_output(process.stderr)
            assert process.wait() == 0, 'sys call failed'


def prun(gfs_file,
         output_file,
         n=mp.cpu_count(),
         working_dir="."):

    logger.info('check consistency of input files')
    gfs_file, working_dir, = _assert_files(gfs_file, working_dir)

    command = (['docker', 'run', '--rm',
                '-v', f'{gfs_file.abspath()}:/root/{gfs_file.basename()}',
                '-v', f'{working_dir.abspath()}:/root', 'gerris',
                'mpirun', '--allow-run-as-root',
                '-np', str(n), 'gerris2D', '-m',
                str(gfs_file.basename())])
    logger.debug('command line : %s' % ' '.join(command))

    logger.info('starting gerris simulation...')
    with open(output_file, 'wb') as f:
        with subprocess.Popen(command,
                              stdout=f,
                              stderr=subprocess.PIPE) as process:
            with process.stderr:
                log_subprocess_output(process.stderr)
            assert process.wait() == 0, 'sys call failed'
    logger.info('gerris simulation finished')


def generate_topo_from_file(xyz_file,
                            topo_name,
                            working_dir="."):

    logger.info('check consistency of input files')
    xyz_file, working_dir, = _assert_files(xyz_file, working_dir)

    command = (['docker', 'run', '--rm',
                '-v', f'{xyz_file.abspath()}:/root/{xyz_file.basename()}',
                '-v', f'{working_dir.abspath()}:/root', 'gerris',
                'bash', '-c',
                f"xyz2kdt -v {topo_name} < {xyz_file.basename()}"])
    logger.debug('command line : %s' % ' '.join(command))

    logger.info('starting converting topo...')
    with subprocess.Popen(command,
                          stderr=subprocess.PIPE) as process:
        with process.stderr:
            log_subprocess_output(process.stderr)
        assert process.wait() == 0, 'sys call failed'
    logger.info('done')


def generate_topo_from_array(x, y, z,
                             topo_name,
                             working_dir="."):

    working_dir = Path(working_dir)
    logger.debug(
        f'checking if working directory ({working_dir.abspath()}) exist')
    assert working_dir.isdir(), "Working directory does not exist"

    command = (['docker', 'run', '--rm',
                '-a', 'STDIN', '-a', 'STDOUT', '-a', 'STDERR',
                '-v', f'{working_dir.abspath()}:/root', 'gerris',
                'xyz2kdt', '-v', topo_name])
    logger.debug('command line : %s' % ' '.join(command))

    logger.info('starting converting topo...')
    xx, yy = np.meshgrid(x, y)

    _, tmp_file = tempfile.mkstemp()
    with open(tmp_file, 'w') as f:
        for line in zip(*map(lambda x: x.flatten(),
                             [xx, yy, z])):
            print(' '.join(map(str, line)), file=f)
    generate_topo_from_file(tmp_file, topo_name)
    Path(tmp_file).remove()
    logger.info('done')


def read_asc(asc_filename):
    header = Path(asc_filename).lines()[:6]
    ncols = int(header[0].split()[1])
    nrows = int(header[1].split()[1])
    cellsize = float(header[4].split()[1])
    x = np.linspace(0, cellsize * nrows, nrows)
    y = np.linspace(0, cellsize * ncols, ncols)
    xx, yy = np.meshgrid(x, y)

    z = np.loadtxt(asc_filename, skiprows=6)
    z = z.reshape((nrows, ncols))
    return xx, yy, z
