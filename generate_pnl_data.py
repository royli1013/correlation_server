"""
Script for generating pnl data
"""
import argparse
import datetime
import multiprocessing
import os
import sys
import time
import numpy as np

# from memory_profiler import profile

from utils.file_utils import write_to_file

INSTRUMENTS = 30  # N
DAYS = 2500  # D
IDEAS = 10  # K


# @profile
def generate_data(dir_name, num_files):
    """
    Generates num_files (n) pnl files in specified directory. Each file contains
    dates, pnl, and turnover. Files are named 'pnl_0', 'pnl_1', ..., 'pnl_n'

    Parameters
    ----------
    dir_name (str): directory to store files
    num_files (int): number of files to generate
    """
    start_time = time.time()
    dates = generate_dates(20090101, DAYS)
    individual_returns = generate_returns(INSTRUMENTS, DAYS, IDEAS)
    total_returns = np.sum(individual_returns, axis=0)

    returns_noise = normal_as_float32((IDEAS, DAYS, INSTRUMENTS)) * 0.01
    observed_signals = individual_returns + returns_noise
    print("Generated returns in {0:.4f}s".format(time.time() - start_time))

    start_time = time.time()
    alpha_idea_indices = np.random.randint(IDEAS, size=num_files, dtype="int8")
    alphas_raw = normal_as_float32((num_files, DAYS, INSTRUMENTS)) * 0.02  # noise
    alphas_raw += np.take(observed_signals, alpha_idea_indices, axis=0)  # noise + signal
    print("Generated raw alphas in {0:.4f}s".format(time.time() - start_time))

    lambdas = np.random.uniform(low=0.0, high=1.0, size=num_files).astype("float32")
    start_time = time.time()
    alphas_smoothed = apply_smoothing(alphas_raw, lambdas)
    del alphas_raw
    print("Applied smoothing in {0:.4f}s".format(time.time() - start_time))

    start_time = time.time()
    pnls = calculate_pnls(alphas_smoothed, total_returns)
    print("Calculated pnls in {0:.4f}s".format(time.time() - start_time))

    start_time = time.time()
    tvrs = calculate_turnovers(alphas_smoothed)
    print("Calculated turnovers in {0:.4f}s".format(time.time() - start_time))

    start_time = time.time()
    write_to_directory_parallel(dir_name, dates, pnls, tvrs)
    print("Wrote to files in {0:.4f}s".format(time.time() - start_time))


def generate_dates(start_date, n):
    """
    Creates array of n weekdays starting at start, inclusive.
    Since n is usually fairly small, we are not doing a lot of optimizations here.

    Parameters
    ----------
    start (int): YYYYMMDD, inclusive
    n (int): number of days requested

    Returns
    -------
    ndarry, of length n, of n weekdays starting at start, inclusive

    """
    start_day = start_date % 100
    start_month = (start_date // 100) % 100
    start_year = start_date // 10000
    dates = []
    cur_date = datetime.date(start_year, start_month, start_day)
    while len(dates) < n:
        if cur_date.weekday() < 5:  # weekday check
            dates.append(cur_date.strftime("%Y%m%d"))
        cur_date += datetime.timedelta(days=1)
    return np.array(dates, dtype="int32")


def generate_returns(instruments, days, k):
    """
    Generates k (days x instruments) matrices. Matrices have mean 0 and standard deviation
    of 0.02 / sqrt(n) for n in 1...k. Not doing a lot of optimizing here since instruments,
    days, and k are all fairly small

    Parameters
    ----------
    instruments (int): number of different instruments
    days (int): number of days
    k (int): number of matrices to generate

    Returns
    -------
    A (k x days x instruments) ndarray
    """
    result = []
    for denom in range(1, k + 1):
        result.append(np.random.normal(0, 0.02 / np.sqrt(denom), (days, instruments)))
    return np.array(result, dtype="float32")


def apply_smoothing(raw_alphas, lambdas):
    """
    Smooths the raw alphas using lambdas as parameters. Smooths using the following function:
        smoothed[0] = alpha[0]
        smoothed[d] = l * smoothed[d-1]  +  sqrt(1 - l**2) * alpha[d]   for d > 0

    Parameters
    ----------
    raw_alphas (ndarray): (n, D, N) where n = number of alphas
                                          D = number of days in each alpha
                                          N = number of instruments in each alpha
    lambdas (ndarray): (n x 1), the lambda too use for each alpha

    Returns
    -------
    A (n x D x N) ndarray of smoothed alphas
    """
    smoothed = np.empty(shape=raw_alphas.shape, dtype="float32")
    # Copy over first day for all alphas
    smoothed[:, 0, :] = raw_alphas[:, 0, :]
    days = raw_alphas.shape[1]
    # Calculate sqrt(1 - l**2) * alpha so we don't have to do it in loop below
    raw_alphas *= np.sqrt(1 - np.square(lambdas))[:, np.newaxis, np.newaxis]
    lambdas_2d = lambdas[:, np.newaxis]
    for i in range(1, days):
        smoothed[:, i, :] = lambdas_2d * smoothed[:, i - 1, :] + raw_alphas[:, i, :]
    return smoothed


def calculate_pnls(alphas, returns):
    """
    Calculates the pnl from alphas given the total instrument returns

    Parameters
    ----------
    alphas (ndarray): (n x D x N) where n = number of alphas
                                        D = number of days in each alpha
                                        N = number of instruments in each alpha
    returns (ndarray): (D x N), the returns for each instrument for each day

    Returns
    -------
    A (n x D) ndarray of pnl for each alpha for each day
    """
    returns_3d = returns[np.newaxis, :, :]
    return np.sum(alphas * returns_3d, axis=2)


def calculate_turnovers(alphas):
    """
    Calculates turnover for given alphas

    Parameters
    ----------
    alphas (ndarray): (n x D x N) where n = number of alphas
                                        D = number of days in each alpha
                                        N = number of instruments in each alpha
    Returns
    -------
    A (n x D) ndarray of turnovers for each alpha for each day
    """
    num_alphas, days, _ = alphas.shape
    turnover = np.empty(shape=(num_alphas, days), dtype="float32")
    turnover[:, 0] = np.zeros(num_alphas)
    turnover[:, 1:] = np.sum(np.abs(np.diff(alphas, axis=1)), axis=2) / \
                      np.sum(np.abs(alphas), axis=2)[:, :-1]
    return turnover


def write_to_directory_parallel(dir_name, dates, pnls, tvrs):
    """
    Writes pnls and tvrs, along with dates, to files in a directory

    Parameters
    ----------
    dir_name (str): name of directory
    dates (ndarray): dates (same for all pnls and tvrs), length D
    pnls (ndarray): (n x D) pnl, where n is the number of files to write to
    tvrs (ndarray): (n x D) turnover, where n is the number of files to write to
    """
    num_files, _ = pnls.shape
    workers = multiprocessing.cpu_count()
    print("Using {} CPUs to write files".format(workers))
    pool = multiprocessing.Pool(processes=workers)
    pool.starmap(write_to_file, [(os.path.join(dir_name, "pnl_" + str(i)),
                                  dates,
                                  pnls[i, :],
                                  tvrs[i, :])
                                 for i in range(num_files)])


def normal_as_float32(size):
    """
    Since we cannot pass dtype to np.random.normal(), it generates float64 by default. For
    generating large amounts of data, using a smaller type can be a lot more efficient, so this
    is a wrapper for generating float32s from a standard normal distribution. Since we also
    cannot pass in dtype for np.random.Generator.normal(), we only support generating from N(0, 1).
    This can be extended to generating from N(mu, sigma) through some data manipulation.

    Parameters
    ----------
    size (tuple): size to generate

    Returns
    -------
    Data sampled from standard normal distribution of appropriate size
    """
    gen = np.random.default_rng()
    return gen.standard_normal(size=size, dtype="float32")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates PNL data and writes to file")
    parser.add_argument("--output_dir", "-o", action="store", required=True)
    parser.add_argument("--num_pnls", "-n", action="store", type=int, required=True)
    parser.add_argument("--force", "-f", action="store_true", default=False)
    args = parser.parse_args(sys.argv[1:])
    dir_name = args.output_dir
    files_to_generate = args.num_pnls
    if not os.path.exists(dir_name):
        print("{} could not be found Creating the directory.".format(dir_name))
        os.makedirs(dir_name)
    if not os.path.isdir(dir_name):
        raise ValueError("{} is not a directory. Please remove it or use a different directory"
                         .format(dir_name))
    if len(os.listdir(dir_name)) > 0:
        if args.force:
            import shutil
            shutil.rmtree(dir_name)
            os.makedirs(dir_name)
        else:
            raise ValueError("Directory not empty and --force not specified.")

    generate_data(dir_name, files_to_generate)
