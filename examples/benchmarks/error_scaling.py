import matplotlib.pyplot as plt
import numpy as np
import schrod
import time


def timing(x, V, n_basis_vec, n_tests=1):

    # Initialize the Schrod
    eqn = schrod.Schrod(x, V)

    # Time the Schrod for different numbers of basis states
    times=[]
    for n in n_basis_vec:
        avg_time = 0
        for i in range(n_tests):
            eqn.set_n_basis(n)
            ti = time.time()
            eqn.solve()
            tf = time.time()
            avg_time += (tf - ti)/n_tests

        times.append(avg_time)

    return times

def error(x, V, n_basis_vec, exact):

    # Initialize the Schrod
    eqn = schrod.Schrod(x, V)

    # Calculate the error
    rel_err=[]
    for n in n_basis_vec:
        eqn.set_n_basis(n)
        eqn.solve()
        lam = eqn.eigs
        err = (np.abs((lam - exact[0:n])/exact[0:n]))[:,0:n_basis_vec[0]]

        rel_err.append(err)

    return np.asarray(rel_err)

if __name__=="__main__":

    # Specify the potential
    x = np.linspace(-5, 5, 200)
    V = 1 / 2 * x ** 2

    # The basis states
    ns = np.logspace(np.log10(4), np.log10(100), 15, dtype=np.int16)
    print("Tests will be run for the following numbers "
          "of basis states:\n",
          ns)

    # -------------- Time --------------
    # Time the evaluation evaluation eigenvalues as a function of the
    # the number of basis states

    times = timing(x, V, ns, n_tests=1)

    # Plotting
    plt.figure(1)
    # The points
    plt.plot(np.log10(ns), np.log10(times), 'bo',
             label="Measured times")

    # The fit line
    m, b = np.polyfit(np.log10(ns), np.log10(times), 1)
    plt.plot(np.log10(ns), m * np.log10(ns) + b, 'r-', lw=2,
             label = "%0.3f $\log_{10}(n_{basis})$ + %0.3f" % (m,b))

    # Plot options
    plt.legend(loc=2)
    plt.xlabel("$\log_{10}(n_{basis})$")
    plt.ylabel("$\log_{10}(seconds)$")

    # -------------- Error --------------
    # Calculate the error in the eigenvalues for the particle in a box
    # as a function of the number of basis states
    #
    # # Exact box state energies
    # n_exact = np.arange(0, np.max(ns))
    # exact_energies = np.asarray([(n+1/2) * w for n in n_exact])
    #
    # err = error(x, V, ns, exact_energies)[:,0,:]
    #
    # # Plots
    # plt.figure(2)
    #
    # for i in range(ns[0]):
    #     # The points
    #     plt.plot(np.log10(ns), np.log10(err[:,i]), 'o-',
    #              label="Measured errors")
    #
    #     # # The fit line
    #     # m, b = np.polyfit(np.log10(ns), np.log10(err[:,i]), 1)
    #     # plt.plot(np.log10(ns), m * np.log10(ns) + b, 'r-', lw=2,
    #     #          label="%0.3f $\log_{10}(n_{basis})$ + %0.3f" % (m, b))
    #
    # # Plot options
    # # plt.legend(loc=2)
    # plt.xlabel("$\log_{10}(n_{basis})$")
    # plt.ylabel("$\log_{10}(err)$")

    # Show the plots
    plt.show()