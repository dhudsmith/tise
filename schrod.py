import numpy as np
from scipy.integrate import simps
import warnings
import collections

""" Schrod: a fast, accurate, and general module for solving 1- and 2- particle Schrodinger equations.
"""


class Schrod:
    """
    A class for representing and solving the time-independent schrodinger
    equation.
    """
    x = None
    V = None
    n_basis = None
    eigs = None
    vecs = None

    x_min = None
    x_max = None
    box_size = None
    _x_center = None

    def __init__(self, x, V, n_basis=20):
        """
        Initialize a time independent schrodinger equation
        :param x: an ndarray. The coordinates at which the potential is evaluated.
        :param V: the potential or potentials to solve. An ndarray
        of shape (n_V, n_x) where n_V is the number of potentials
        and n_x is the length of x.
        :param n_basis:
        """
        self.x = x
        self.V = V
        self.n_basis = n_basis

        self.x_min = x[0]
        self.x_max = x[-1]
        self.box_size = np.abs(self.x_max - self.x_min)
        self._x_center = self.x_min + self.box_size / 2.

    def solve(self, verbose=False):
        if verbose:
            print("Calculating the Hamiltonian matrices...")
        Hs = self._H(verbose)

        if verbose:
            print("Diagonalizing the Hamiltonian matrices...")

        self.eigs, self.vecs = np.linalg.eigh(Hs, UPLO='L')

    def solve_to_tol(self, n_eig, tol=1e-6, n_init=5, n_max=50, n_step=5, verbose=False):
        """
        Increase the basis size until the maximum change among the lowest
        <n_eig> eigenvalues is less than <tol>
        :param n_eig: The number of eigenvalues (lowest) to check for convergence.
        :param tol: The desired maximum relative error in the output
        :param n_init: The initial number of basis states. Must satisfy n_init >= n_eig
        :param n_max: The maximum number of basis states to include before stopping.
        :param n_step: The number of basis states added in each convergence test.
        :return: A tuple with the following information (A, B, C):
            A: Boolean. True if maximum measured relative error less than or equal to <tol>
            B: The number of basis states included when convergence reached.
            C: The measured relative error
        """

        # The initial truncation
        self.set_n_basis(n_init)
        self.solve()
        eigs = self.eigs[..., 0:n_eig]
        err = 1

        # The maximum relative error in the lowst <n_eig> eigenvalues
        measured_tol = 1  # the max rel. err. of the eigenvalues
        n = n_init
        passed = False
        while (not passed) and (n+n_step <= n_max):
            n += n_step

            self.set_n_basis(n)
            self.solve()
            eigs_new = self.eigs[..., 0:n_eig]

            err = np.abs((eigs - eigs_new) / 0.5 / (eigs + eigs_new))
            measured_tol = np.max(err)
            eigs = eigs_new

            if verbose:
                print("Number of basis states: %i \n Measured error: %.2e" % (n, measured_tol))

            if measured_tol <= tol:
                passed = True

        if not passed:
            warnings.warn("Unable to achieve desired tolerance of %.2e.\n"
                          "Achieved a tolerance of %.2e.\n"
                          "Try increasing the maximum number of basis states." % (tol, measured_tol))

        solution = collections.namedtuple('Solution',
                                          ['eig_errs', 'n_basis_converged', 'passed'])

        return solution(err, n, passed)



    def psi(self):
        basis_vec = np.arange(1, self.vecs.shape[-1] + 1)

        return np.dot(self.vecs.transpose((0, 2, 1)),
                      self._psi0(basis_vec, self.x))

    def prob(self):
        return self.psi() ** 2

    # Get functions
    def get_x(self):
        return self.x

    def get_V(self):
        return self.V

    def get_n_basis(self):
        return self.n_basis

    def get_eigvals(self):
        return self.eigs

    def get_eigvecs(self):
        return self.vecs

    # Set functions
    def set_x(self, x):
        self.x = x
        self.x_min = x[0]
        self.x_max = x[-1]
        self.box_size = self.x_max = self.x_min
        self._x_center = self.x_min + self.box_size / 2.

    def set_V(self, V):
        self.V = V

    def set_n_basis(self, n_basis):
        self.n_basis = n_basis

    # Private functions:
    def _H(self, verbose=False):
        n_matels = self.n_basis * (self.n_basis + 1) / 2

        # initialize an empty hamiltonian(s)
        h=0

        if len(self.V.shape) is 2:
            h = np.zeros((self.V.shape[0], self.n_basis, self.n_basis))
        elif len(self.V.shape) is 1:
            h = np.zeros(( self.n_basis, self.n_basis))
        for m in range(self.n_basis):
            for n in range(m + 1):
                h[..., m, n] = self._Vmn(m, n)

                # Print a status
                n_sofar = (m + 1) * m / 2 + n + 1
                percent = n_sofar / n_matels * 100

                if verbose:
                    print("\r  Status: %0.2f %% complete" % percent, end='')

        if verbose:
            print("")

        return h + np.diag(self._E0(np.arange(1, self.n_basis + 1)))

    def _psi0(self, n, x):
        """
        Evaluate the nth box state at x
        :param n: array-like, 1-indexed state labels
        :param x: array-like, positions between -1 and 1
        :return: an array of shape (len(n), len(x))
        """
        kn = n * np.pi / self.box_size

        return np.sqrt(2 / self.box_size) * \
               np.sin(np.outer(kn, x - self._x_center + self.box_size / 2))

    def _E0(self, n):
        """
        The nth energy level in the box
        :param n: the state label
        :return: the energy
        """
        return n ** 2 * np.pi ** 2 / (2. * self.box_size ** 2)

    def _matel_integrand(self, m, n):
        """
        The n,m matrix element of the V potential evaluated at the x coordinates
        :param n:   the row index
        :param m:   the column index
        :param x:   array-like, a vector of x coordinates
        :param V:   array-like, an array of potential values. The rows correspond to
                    the entries in x. The columns correspond to different potentials
        :return:    the integrand of the matrix element
        """
        return self._psi0(m + 1, self.x) * self._psi0(n + 1, self.x) * self.V

    def _Vmn(self, m, n):
        return simps(x=self.x, y=self._matel_integrand(m, n), axis=-1)




if __name__ == "__main__":
    # Specify the potential
    x = np.linspace(-5, 5, 200)
    V = 3*np.sin(5*x)

    # Create and solve Schrodinger's equation
    eqn = Schrod(x, V)
    sol = eqn.solve_to_tol(n_eig=5, tol=1e-10, n_init=50, n_max=200)

    # Print the first five eigenvalues
    print("Eigenvalues: ", eqn.eigs[0:5])
    print("Error estimate: ", sol.eig_errs)
    print("Number of basis states at convergence: ", sol.n_basis_converged)