"""
Smarch - random sampling of propositional formula solutions
Version - 0.1
"""


import random
from subprocess import getoutput
import pycosat
import os
import time
import sys
import getopt
import shutil

from anytree import AnyNode
from anytree.exporter import JsonExporter
from anytree.importer import JsonImporter

srcdir = os.path.dirname(os.path.abspath(__file__))
SHARPSAT = srcdir + '/samplers/sharpSATSMARCH/Release/sharpSAT'
MARCH = srcdir + '/march_cu/march_cu'



def read_dimacs(dimacsfile_):
    """parse variables and clauses from a dimacs file"""

    _features = list()
    _clauses = list()
    _vcount = '-1'  # required for variables without names

    with open(dimacsfile_) as f:
        for line in f:
            # read variables in comments
            if line.startswith("c ind"): #we do not deal with independant variables produced by other tool - modification w.r.t original SMARCH
                continue
            elif line.startswith("c"):
                line = line[0:len(line) - 1]
                _feature = line.split(" ", 4)
                del _feature[0]
                # handling non-numeric feature IDs -  modification w.r.t original SMARCH
                if (_feature[0].isdigit()):
                  _feature[0] = int(_feature[0])
                else:
                  # num_filter = filter(_feature[0].isdigit(), _feature[0])
                  num_feature = "".join(c for c in _feature[0] if c.isdigit())
                  _feature[0] = int(num_feature)
                _features.append(tuple(_feature))
            # read dimacs properties
            elif line.startswith("p"):
                info = line.split()
                _vcount = info[2]
            # read clauses
            else:
                info = line.split()
                if len(info) != 0:
                    _clauses.append(list(map(int, info[:len(info)-1])))
                    #_clauses.append(line.strip('\n'))

    return _features, _clauses, _vcount


def read_constraints(constfile_, features_):
    """read constraint file. - means negation"""

    _const = list()

    if os.path.exists(constfile_):
        names = [i[1] for i in features_]
        with open(constfile_) as file:
            for line in file:
                line = line.rstrip()
                data = line.split()
                if len(data) != 0:
                    clause = list()

                    error = False
                    for name in data:
                        prefix = 1
                        if name.startswith('-'):
                            name = name[1:len(name)]
                            prefix = -1

                        if name in names:
                            i = names.index(name)
                            clause.append(features_[i][0] * prefix)
                        else:
                            error = True
                            clause.append(name)

                    if not error:
                        _const.append(clause)
                        print("Added constraint: " + line + " " + str(clause))
                    else:
                        print("Feature not found" + str(clause))

                    # line = line[0:len(line) - 1]
                    # prefix = ''
                    # if line.startswith('!'):
                    #     line = line[1:len(line)]
                    #     prefix = '-'
                    #
                    # # filter features that does not exist
                    # if line in names:
                    #     i = names.index(line)
                    #     _const.append(prefix + features_[i][0])
                    #     print("Added constraint: " + prefix + features_[i][0] + "," + prefix + features_[i][1])
    else:
        print("Constraint file not found")

    return _const


def get_var(flist, features_):
    """convert feature names into variables"""

    _const = list()
    names = [i[1] for i in features_]

    for feature in flist:
        #feature = feature[0:len(feature) - 1]
        prefix = 1
        if feature.startswith('-'):
            feature = feature[1:len(feature)]
            prefix = -1

        # filter features that does not exist
        if feature in names:
            i = names.index(feature)
            _const.append(prefix * features_[i][0])

    return _const


def gen_dimacs(vars_, clauses_, constraints_, outfile_):
    """generate a dimacs file from given clauses and constraints"""

    f = open(outfile_, 'w')
    f.write('p cnf ' + vars_ + ' ' + str(len(clauses_) + len(constraints_)) + '\n')

    for cl in clauses_:
        #f.write(cl + '\n')
        f.write(" ".join(str(x) for x in cl) + ' 0 \n')

    for ct in constraints_:
        if isinstance(ct, (list,)):
            line = ""
            for v in ct:
                line = line + str(v) + " "
            f.write(line + '0 \n')
        else:
            f.write(str(ct) + ' 0 \n')

    f.close()


def count(dimacs_, constraints_):
    """count dimacs solutions with given constraints"""

    _tempdimacs = os.path.dirname(dimacs_) + '/count.dimacs'
    _features, _clauses, _vcount = read_dimacs(dimacs_)

    gen_dimacs(_vcount, _clauses, constraints_, _tempdimacs)
    res = int(getoutput(SHARPSAT + ' -q ' + _tempdimacs))

    return res


def checkSAT(dimacs_, constraints_):
    """check satisfiability of given formula with constraints"""
    _features, _clauses, _vcount = read_dimacs(dimacs_)
    cnf = _clauses + constraints_
    s = pycosat.solve(cnf)

    if s == 'UNSAT':
        return False
    else:
        return True


def sample(vcount_, clauses_, n_, wdir_, const_=(), cache_=False, quiet_=False, samplefile_=""):
    """sample configurations"""

    if not os.path.exists(wdir_):
        os.makedirs(wdir_)

    samples = list()

    # partition space by cubes and count number of solutions for each cube
    def partition(assigned_, current_, tree_):
        _total = 0
        _counts = list()
        _cubes = list()
        _freevar = list()
        _dimacsfile = wdir_ + '/dimacs.smarch'
        _cubefile = wdir_ + '/cubes.smarch'

        # create dimacs file regarding constraints
        gen_dimacs(vcount_, clauses_, assigned_, _dimacsfile)

        # execute march to get cubes
        res = getoutput(MARCH + ' ' + _dimacsfile + ' -d 5 -# -o ' + _cubefile)
        out = res.split("\n")

        # print march result (debugging purpose)
        #print(out)

        if out[7].startswith('c all'):
            _freevar = out[5].split(": ")[1].split()

        with open(_cubefile) as f:
            for _line in f:
                _cube = list(_line.split())
                if 'a' in _cube:
                    _cube.remove('a')
                if '0' in _cube:
                    _cube.remove('0')

                _cubes.append(_cube)

        # execute sharpSAT to count solutions
        for _cube in _cubes:
            gen_dimacs(vcount_, clauses_, assigned_ + _cube, _dimacsfile)
            res = int(getoutput(SHARPSAT + ' -q ' + _dimacsfile))
            # print(res)
            _total += res
            _counts.append(res)

        # double check if all variables are free (nonempty freevar means all free)
        if _total != pow(2, len(_freevar)):
            _freevar.clear()

        # set total number of solutions
        current_.count = _total

        if tree_:
            # extend tree - do not extend if all variables are free
            if len(_freevar) == 0:
                for _i in range(0, len(_counts)):
                    _node = AnyNode(parent=current_, count=_counts[_i], cube=_cubes[_i])

        return [_freevar, _counts, _cubes, _total]

    # generate n random numbers for sampling
    def get_random(rcount_, total_):
        def gen_random():
            while True:
                yield random.randrange(1, total_, 1)

        def gen_n_unique(source, n__):
            seen = set()
            seenadd = seen.add
            for i in (i for i in source() if i not in seen and not seenadd(i)):
                yield i
                if len(seen) == n__:
                    break

        return [i for i in gen_n_unique(gen_random, min(rcount_, int(total_ - 1)))]

    # select a cube based on given random number
    def select_cube(counts_, cubes_, number_):
        _terminate = False
        _index = -1
        _i = 0

        for c in counts_:
            if number_ <= c:
                _index = _i
                if c == 1:
                    _terminate = True
                break
            else:
                number_ -= c
            _i += 1

        return cubes_[_index], number_, _terminate

    # traverse the cube tree based on given random number (requires cache_=True)
    def traverse_cube(current_, number_):
        _assigned = list()
        _terminate = False
        #_assigned = _assigned + _current.cube

        while len(current_.children) != 0 or current_.count != 1:
            for node in current_.children:
                if number_ <= node.count:
                    _assigned = _assigned + node.cube
                    current_ = node
                    break
                else:
                    number_ -= node.count
            break

        if current_.count == 1:
            _terminate = True

        return _assigned, number_, _terminate, current_

    # assign free variables without recursion
    def set_freevar(freevar_, number_):
        _vars = list()

        for v in freevar_:
            if number_ % 2 == 1:
                _vars.append(v)
            else:
                _vars.append('-'+v)
            number_ //= 2

        return _vars

    clauses_ = clauses_ + const_

    root = AnyNode(count=-1, cube=[])
    if not quiet_:
        print("Counting - ", end='')
    freevar = partition([], root, cache_)

    if not quiet_:
        print("Total configurations: " + str(freevar[3]))

    start_time = time.time()

    # generate random numbers
    rands = get_random(n_, freevar[3])

    if samplefile_ != "":
        f = open(samplefile_, "w")
    else:
        f = ""

    i = 0

    # sample for each random number
    for r in rands:
        if not quiet_:
            print("Sampling " + str(i) + " with " + str(r) + " - ", end='')
        sample_time = time.time()

        # initialize variables
        number = r
        assigned = list()
        current = root

        if len(freevar[0]) != 0:  # all variables free, sampling done
            assigned = assigned + set_freevar(freevar[0], int(number))
            #print("all free")
            terminate = True
        else:  # select cube to recurse
            if cache_:
                cube, number, terminate, current = traverse_cube(current, number)
            else:
                cube, number, terminate = select_cube(freevar[1], freevar[2], number)
            assigned = assigned + cube

            if len(cube) == 0:
                print("ERROR: cube not selected")
                exit()

        # recurse
        while not terminate:
            r_freevar = partition(assigned, current, cache_)

            if len(r_freevar[0]) != 0:  # all variables free, sampling done
                assigned = assigned + set_freevar(r_freevar[0], int(number))
                #print("all free")
                terminate = True
            else:  # select cube to recurse
                if cache_:
                    cube, number, terminate, current = traverse_cube(current, number)
                else:
                    cube, number, terminate = select_cube(r_freevar[1], r_freevar[2], number)
                assigned = assigned + cube

                if len(cube) == 0:
                    print("ERROR: cube not selected")
                    exit()

        # verify if sample is valid and assign dead variables using pycosat
        assigned = list(map(int, assigned))
        aclause = [assigned[i:i+1] for i in range(0, len(assigned))]
        cnf = clauses_ + aclause
        s = pycosat.solve(cnf)

        # print(s)

        # sdimacs = sdir + "/" + str(i) + ".dimacs"
        # gen_dimacs(vcount_, clauses_, assigned, sdimacs)
        # getoutput("minisat " + sdimacs + " " + sdir + "/" + str(i) + ".sol")
        # res = int(getoutput(SHARPSAT + ' -q ' + sdimacs))
        # print(res)

        # print(len(s))

        if s == 'UNSAT':
            print("ERROR: Sample Invalid")
            exit(1)
        else:
            if samplefile_ == "":
                samples.append(set(s))
            else:
                for v in s:
                    f.write(str(v))
                    f.write(",")
                f.write("\n")

        if not quiet_:
            print("sampling time: " + str(time.time() - sample_time))

        i += 1

    if not quiet_:
        print("--- total time: %s seconds ---" % (time.time() - start_time))

    if cache_:
        exporter = JsonExporter()
        with open(wdir_ + "/tree.json", 'w') as file:
            file.write(exporter.export(root))
            file.close()
    else:
        shutil.rmtree(wdir_)

    if samplefile_ != "":
        f.close()

    return samples


# test script
# n = 10
# target = "axtls_2_1_4"
#
# dimacs = "/home/jeho/kmax/kconfig_case_studies/cases/" + target + "/build/kconfig.dimacs"
# constfile = os.path.dirname(dimacs) + "/constraints.txt"
# wdir = os.path.dirname(dimacs) + "/smarch"
#
# features, clauses, vcount = read_dimacs(dimacs)
# const = read_constraints(constfile, features)
#
# samples = sample(vcount, clauses, n, wdir, const, True, 1)


# run script
if __name__ == "__main__":
    # get external location for sharpSAT and march if needed
    if os.path.exists(srcdir + "/links.txt"):
        with open(srcdir + "/links.txt") as f:
            for _line in f:
                link = list(_line.split('='))
                if len(link) != 0 and link[0][0] != '#':
                    if link[0] == "SHARPSAT":
                        SHARPSAT = link[1]
                    elif link[0] == "MARCH":
                        MARCH = link[1]

    # check sharpSAT and march_cu existence
    if not os.path.exists(SHARPSAT):
        print("ERROR: sharpSAT not found")

    if not os.path.exists(MARCH):
        print("ERROR: March solver not found")

    # get parameters from console
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:o:q", ['help', "cfile=", "odir=", 'quiet'])
    except getopt.GetoptError:
        print('smarch.py -c <constfile> -o <outputdir> -q| <dimacsfile> <samplecount>')
        sys.exit(2)

    if len(args) < 2:
        print('smarch.py -c <constfile> -o <outputdir> -q | <dimacsfile> <samplecount>')
        sys.exit(2)

    dimacs = args[0]
    base = os.path.basename(dimacs)
    target = os.path.splitext(base)[0]

    n = int(args[1])

    print('Input file: ', dimacs)
    print('Number of samples: ', n)

    wdir = os.path.dirname(dimacs) + "/smarch"
    constfile = ''
    samplefile = ""
    quiet = False
    cache = False
    out = False

    for opt, arg in opts:
        if opt == '-h':
            print('smarch.py -c <constfile> -o <outputdir> -s | <dimacsfile> <samplecount>')
            sys.exit()
        elif opt in ("-c", "--cfile"):
            constfile = arg
            print("Consraint file: " + constfile)
        elif opt in ("-o", "--odir"):
            odir = arg
            wdir = odir + "/smarch"
            samplefile = odir + "/" + target + "_" + str(n) + ".samples"
            out = True
            print("Output directory: " + wdir)
        elif opt in ("-l", "--log"):
            start = int(arg)
            cache = True
        elif opt in ("-q", "--quiet"):
            quiet = True
        else:
            print("Invalid option: " + opt)

    features, clauses, vcount = read_dimacs(dimacs)
    const = list()
    if constfile != '':
        read_constraints(constfile, features)

    samples = sample(vcount, clauses, n, wdir, const, cache, quiet, samplefile)

    if out:
        # f = open(wdir + "/" + target + "_" + str(n) + ".samples", 'w')
        # for s in samples:
        #     for v in s:
        #         f.write(str(v))
        #         f.write(",")
        #     f.write("\n")
        # f.close()

        print('Output samples created on: ', samplefile)
