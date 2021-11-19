
import sys
import os
import os.path
import glob
import argparse
import textwrap
import importlib


# list domains
domains = []
for path in sorted(
        glob.glob(
            os.path.join(
                os.path.dirname(__file__),"*",""))):

    name = os.path.basename(os.path.dirname(path))
    if "__" not in name:
        domains.append(name)

assert "blocksworld-3ops" in domains


parser = argparse.ArgumentParser(
    formatter_class = argparse.RawTextHelpFormatter,
    description =
    textwrap.fill(
        "Generates a problem file for a given domain and a set of hyperparameters. "
        "Depending on the domain, it also produces a domain file (e.g., ADL domain compiled to strips). "
        "In the default behavior, it generates the file(s) to a specified location, then print "
        "the absolute pathname of the problem file and the domain file in two separate lines. "
        "The second line (the domain file) can be a file generated by the generator, "
        "or a fixed pddl file that is shared by problems. "
        "When --output STDOUT is given, the output is printed to the standard output (see options for --output). ", 100)
)


parser.add_argument("domain",
                    metavar="domain",
                    nargs="?",  # note: for --help and --helpall to work
                    choices=domains,
                    help="domain name, one of: \n" + textwrap.fill(", ".join(domains), 100))

parser.add_argument("--output-directory","-d",
                    default="output",
                    metavar="DIRNAME",
                    help=
                    "Directory to store the generated files. \n"
                    "If the directory does not exist, it creates it first (including the parents). \n"
                    )

parser.add_argument("--output","-o",
                    metavar="FILENAME1",
                    help=
                    "If given, override the default name handling for problem file generation. \n"
                    "If the pathname is absolute, it is used as it is; DIRNAME is ignored. \n"
                    "If the pathname is relative, it is seen as a path relative to DIRNAME. \n"
                    "\n"
                    "If not given, the file is stored under DIRNAME and as {hash}.pddl , where \n"
                    "{hash} is a md5 hash of the parameters given to each generator. \n"
                    "\n"
                    "If the generator also generates a compiled domain file, it is written to a file with \n"
                    "a suffix {basename}-domain.pddl where {basename} is the basename of the problem file. \n"
                    "You can override this behavior with --output-domain. \n"
                    "\n"
                    "If the argument is STDOUT, it writes to the standard output. \n"
                    "If the argument is STDOUT for a domain that also generates a domain file, two outputs are \n"
                    "separated by a separator specified by --separator option. \n"
                    "\n"
                    "In all cases, the output contains a meta-information of how the generator was called \n"
                    "in a form of Lisp-style comment with each line starting with ;; . \n"
                    "The format mimicks File-Local Variable of Emacs \n"
                    "(see https://www.gnu.org/software/emacs/manual/html_node/emacs/Specifying-File-Variables.html). \n"
                    "\n"
                    "It contains several fields: \n"
                    "The first line contains 'pddl-generators:'. \n"
                    "'command:' field contains the exact command line used to run the generator, \n"
                    "'dict:' field which contains a dictionary which was parsed from the command line, and \n"
                    "'date:' field contains the date of creation. \n"
                    "The last line contains 'end:'. \n"
                    )

parser.add_argument("--output-domain",
                    metavar="FILENAME2",
                    help=
                    "If given, override the default name handling for domain file generation. \n"
                    "If the pathname is absolute, it is used as it is; DIRNAME is ignored. \n"
                    "If the pathname is relative, it is seen as a path relative to DIRNAME. \n"
                    "\n"
                    "If missing and the generator generates a new domain file for each problem instance, \n"
                    "the filename defaults to {basename}-domain.pddl \n"
                    "where {basename} is the basename of FILENAME1. \n"
                    "\n"
                    "If missing and the domain comes with a shared domain file, \n"
                    "the value is set to the path of the domain file inside pddl-generator source tree \n"
                    "(likely under site-packages/). \n"
                    "\n"
                    "Finally, if given while the domain comes with a shared domain file, \n"
                    "it copies the domain file to the specified location. \n"
                    )

parser.add_argument("--separator",
                    default=";; domain file",
                    help=
                    "See --output. When the generator produces both a problem and a domain file, \n"
                    "and if the --output is specified as STDOUT, two files are concatenated with \n"
                    "a line containing the string specified by this option. ")

parser.add_argument("--seed","-s",
                    type=int,
                    default=42,
                    help="Random seed.")

parser.add_argument("--helpall",
                    action="store_true",
                    help="Generate help messages for all domains.")

parser.add_argument("--list","-l",
                    action="store_true",
                    help="List available domains.")

parser.add_argument("--debug",
                    action="store_true",
                    help="Enable a more verbose debugging mode.")

# parser.add_argument("--remove-trivial",
#                     action="store_true",
#                     help="Remove an instance whose initial state already satisfies its goal condition.\n"
#                     " NOT IMPLEMENTED YET, work in progress.")
#
# parser.add_argument("--remove-cost",
#                     action="store_true",
#                     help="Remove action cost from the generated instances.\n"
#                     " Also from the domain, if it generates a domain compiled from ADL.\n"
#                     " NOT IMPLEMENTED YET, work in progress.")
#
# parser.add_argument("--remove-delete",
#                     action="store_true",
#                     help="Remove delete effects from the domain, if it generates a domain compiled from ADL.\n"
#                     " NOT IMPLEMENTED YET, work in progress.")


parser.add_argument("rest",
                    nargs="*",
                    help="Remaining command line arguments for each domain.")


def main(args):

    if args.helpall:
        helpall()
        return
    else:
        if args.domain is None:
            parser.error("Missing a required argument: domain")

    dispatch(args)

    pass


def helpall():

    for domain in domains:
        print(f"\n\n################################ {domain} ################################\n")
        try:
            m = importlib.import_module("pddl_generators."+domain)
        except ModuleNotFoundError as e:
            print(f"ModuleNotFoundError while loading pddl_generators.{domain}, probably the domain is not supported by this uniform api yet.")
            continue
        except Exception as e:
            print(e)
            continue


        try:
            assert hasattr(m, "parser"),        f"the module {m.__name__} lacks a parser"
            assert hasattr(m, "main"),          f"the module {m.__name__} lacks a main function"
            assert hasattr(m, "domain_file"),   f"the module {m.__name__} lacks domain_file attribute"
            m.parser.print_help()
        except AssertionError as e:
            print(e)
            continue



def dispatch(args):
    try:
        m = importlib.import_module("pddl_generators."+args.domain)
    except ModuleNotFoundError as e:
        print(f"ModuleNotFoundError while loading {args.domain}, probably the domain is not supported by this uniform api yet.")
        sys.exit(1)

    try:
        assert hasattr(m, "parser"),        f"the module {m.__name__} lacks a parser"
        assert hasattr(m, "main"),          f"the module {m.__name__} lacks a main function"
        assert hasattr(m, "domain_file"),   f"the module {m.__name__} lacks domain_file attribute"
        args2 = m.parser.parse_args(args.rest)
    except AssertionError as e:
        print(e)
        sys.exit(1)

    m.main(args, args2)


if __name__ == "__main__":
    main(parser.parse_args())

