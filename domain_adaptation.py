'''Functions to prepare the domain adaptation experiments'''
from __future__ import with_statement

from optparse import OptionParser
import csv
import math
import os
import random
import re
import subprocess
import sys
import tempfile

import matplotlib
matplotlib.use('TkAgg')      # backend
import matplotlib.pyplot as pyplot
import simplejson

def plot_err(ms, mt, jsonfile):
    data = simplejson.loads(open(jsonfile).read())
    X = [0.05*x for x in range(20)]
    Y = []
    beta = float(mt) / (ms + mt)
    for alpha in X:
        key = str((ms, mt, alpha))
        acc = data[key]/100
        err = 1 - acc
        Y.append(err)
    l = str(ms) if mt==2500 else str(mt)
    mark = {'250':'-o', '500':'-s', '1000':'-*', '2000':'-D'}
    pyplot.plot(X, Y, mark[l], label=l)
    
def plot_bound(ms, mt, zeta, fix):
    X = [0.1*x for x in range(11)]
    Y = []
    beta = float(mt) / (ms + mt)
    for alpha in X:
        Y.append(bound(alpha,beta, ms+mt, zeta))
    l = str(ms) if mt==2500 else str(mt)
    mark = {'250':'-o', '500':'-s', '1000':'-*', '2000':'-D'}
    pyplot.plot(X, Y, mark[l], label=l)

def plot_curve(curve, zeta, fix):
    '''plots the curve given zeta. Fix says which sample size is fixed
    (S or T)'''
    S = [2500]
    T = [250, 500, 1000, 2000]
    if fix == 'T': S,T = T,S
    for ms in S:
        for mt in T:
            if curve == 'bound':
                plot_bound(ms, mt, zeta, fix)
            else:               # assume jason file
                plot_err(ms, mt, curve)
    pyplot.legend()
    pyplot.axis([0,1,0,1])
    pyplot.show()

def bound(alpha, beta, m, zeta=1):
    # we have 28 features
    C = 1601
    C = 28 + 1
    return math.sqrt((alpha**2/beta + (1-alpha)**2/(1-beta))*C/m)+(1-alpha)*zeta

def sample_category(data, category, N):
    '''extract a sample of N reviews from category'''
    pass

def relabel_and_combine(domain0, domain1):
    '''change all the labels in dataset to match label'''
    label = 'label_useful_extreme_percentile'
    outcsv = open('relabeled.csv', 'w')
    reader0 = csv.DictReader(open(domain0))
    # get fieldnames manually for python 2.5
    first_row = reader0.next()
    fieldnames = sorted(first_row)
    print >>outcsv, ','.join(fieldnames)
    writer = csv.DictWriter(outcsv, fieldnames)
    # write the first row modified.
    first_row[label] = 0
    writer.writerow(first_row)
    # relabel domain 0
    for r in reader0:
        r[label] = 0
        writer.writerow(r)
    # relabel domain 1
    reader1 = csv.DictReader(open(domain0))
    for r in reader1:
        r[label] = 1
        writer.writerow(r)

def output_weight_file(alpha, ms, mt, fpath=None):
    '''produce a file with ms copies of (1-alpha) and mt copies of
    alpha. One weight per line. The output file is
    msS+mtT-alpha.wgt'''
    beta = float(mt) / (ms + mt)
    if fpath is None:
        fpath = "%sS+%sT-%s.wgt" % (ms, mt, alpha)
    outfile = open(fpath, 'w')
    source_weight = '%s\n' % ((1-alpha)/(1-beta))
    print >>outfile, source_weight*ms, # ',' to avoid extra newline
    target_weight = '%s\n' % (alpha/beta)
    print >>outfile, target_weight*mt
    outfile.close()

def combine_domains(S, T, ms, mt):
    '''Produces a set with reviews from both domains with ms source
    reviews and mt target reviews.'''
    mS = random.sample(open(S).readlines()[1:], ms)
    mT = random.sample(open(T).readlines()[1:], mt)

    return mS + mT

# For example, to run an auto experiment do:
# python domain_adaptation.py --auto experiment_data/adapt_amazon_to_yelp_2 experiment_data/adapt_amazon_to_yelp_2/yelp_dense_adaptation_test.svm_problem --combine experiment_data/adapt_amazon_to_yelp_2/amazon_dense_adaptation_labeled.csv experiment_data/adapt_amazon_to_yelp_2/yelp_dense_adaptation_labeled.csv

ALPHAS = [x*0.05 for x in xrange(20)]
M_Ts = [250, 500, 1000, 2000]
M_Ss = [250, 500, 1000, 2000]
SVM_TRAIN_CMD = "external/libsvm-weights-3.0/svm-train -t 0 -W %s %s %s"
SVM_TEST_CMD = "external/libsvm-weights-3.0/svm-predict %s %s /dev/null"

def run_translate_to_svm(infile_path):
    outfile_path = "%s.svm_problem" % infile_path.split('.')[0]
    translate_cmd = "python features_to_svm_problem.py label_useful_extreme_percentile"
    subprocess.check_call(translate_cmd.split(' '), stdin=open(infile_path), stdout=open(outfile_path, 'w'))
    return outfile_path

def run_auto_experiment(options):
    s,t = options.combine
    header = open(s).readlines()[0].strip()
    
    params_to_accuracy = {}
    
    prefix_path, test_file_path = options.auto
    
    # Make a place to put the model... don't know why tempfile is not working
    model_path = os.path.join(prefix_path, "tmp_model")
    open(model_path, 'w').close()
    
    def run_one_experiment(options, ms, mt, alpha):
        with open(os.path.join(prefix_path, '%sS+%sT.csv' % (ms, mt)), 'w') as f:
            print >>f, header
            for line in combine_domains(s, t, ms, mt):
                print >>f, line.strip()
            f.flush()
            svm_input_file_path = run_translate_to_svm(f.name)
        
        weightpath = os.path.join(prefix_path, '%sS+%sT-%s.wgt' % (ms, mt, alpha))
        output_weight_file(alpha, ms, mt, fpath=weightpath)

        svm_results_path = os.path.join(prefix_path, '%sS+%sT-%s.results' % (ms, mt, alpha))        
        svm_cmd = SVM_TRAIN_CMD % (weightpath, svm_input_file_path, model_path)
        print "Executing %s" % svm_cmd
        subprocess.check_call(svm_cmd.split(' '), stdout=open(svm_results_path, 'w'))
        
        # save stdout in a tempfile
        tf_fd, tf_path = tempfile.mkstemp()
        svm_test_cmd = SVM_TEST_CMD % (test_file_path, model_path)
        print "Executing %s" % svm_test_cmd
        subprocess.check_call(svm_test_cmd.split(' '), stdout=open(tf_path, 'w'))
        
        # record the accuracy
        accuracy_line = open(tf_path, 'r').readlines()[-1]
        acc = float(re.findall("Accuracy = (.*)\% .*", accuracy_line)[0])
        params_to_accuracy[str((ms, mt, alpha))] = acc
        
        # kill tempfiles (so that we don't run out of file descriptors in the really bad case)
        os.close(tf_fd)

    ms = 2500
    for mt in M_Ts:
        for alpha in ALPHAS:
            run_one_experiment(options, ms, mt, alpha)
    

    mt = 2500
    for ms in M_Ss:
        for alpha in ALPHAS:
            run_one_experiment(options, ms, mt, alpha)
    
    return params_to_accuracy

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--combine', nargs=2,
                      help='Combine source and target into one data set.' \
                          ' Arguments: sourcefile targetfile.' \
                          ' Options -s and -t are required with this.' \
                          ' Output saved to msS+mtT.csv')
    parser.add_option('-s',
                      help='Number of examples from the source domain')
    parser.add_option('-t',
                      help='Number of examples from the target domain')
    relabel_help='''Combine both domains changing the label to 0 for
               the first domain and 1 for the second one. Arguments:
               domain0.csv domain1.csv. Useful to create input data
               for the linear classifier that learns the domain of a
               review. The error of this classifier is then used as an
               estimate of the distance between the distributions of
               the domains.'''
    parser.add_option('--relabel', nargs=2, help=relabel_help)
    alpha_help='''Expecify alpha to be used for the alpha-error. If
    this is epecified a .wgt file will be generated to pass to libsvm
    during training. Output saved in msS+mtT-alpha.wgt'''
    parser.add_option('-a', '--alpha', help=alpha_help)
    parser.add_option('--auto', nargs=2, default=None,
        help="Automatically generate a bunch of combined files for "
             "default experiment parameters in the given directory (first argument) "
             "using the test file given as the second arg.")
    parser.add_option('--plot', nargs=3,
                      help='plots a curve given zeta and '
                      'fixing either S or T. Arguments: curve zeta {S|T}.'
                      ' curve can be either "bound" or a filename with '
                      'json data to be plotted')
    
    options, args = parser.parse_args()
    if options.auto is not None and options.combine:
        params_to_accuracy = run_auto_experiment(options)
        simplejson.dump(params_to_accuracy, open('params_to_accuracy.json', 'w'))
    elif options.combine:
        s,t = options.combine
        if not options.s or not options.t:
            print 'ms and mt are required when combining domains. See -h'
            sys.exit(1)
        ms, mt = int(options.s), int(options.t)
        outfile = open('%sS+%sT.csv' % (ms, mt), 'w')
        # print header first. don't use csv dict reader to make it
        # simpler
        header = open(s).readlines()[0].strip()
        print >>outfile, header
        for x in combine_domains(s, t, ms, mt):
            print >>outfile, x.strip()
    elif options.relabel:
        domain0, domain1 = options.relabel
        relabel_and_combine(domain0, domain1)
    elif options.alpha:
        if not options.s or not options.t:
            print 'ms and mt are required when generating a wieght file. See -h'
            sys.exit(1)
        ms, mt = int(options.s), int(options.t),
        output_weight_file(float(options.alpha), ms, mt)
    elif options.plot:
        curve, zeta, fixed = options.plot
        plot_curve(curve, float(zeta), fixed)

