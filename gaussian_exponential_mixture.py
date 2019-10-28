import math
from copy import deepcopy
import numpy as np
from scipy import stats


class GaussianExponentialParameters:
    """Holds the parameters used in GaussianExponentialMixture.

    This class allows for access to parameters by name, pretty-printing,
    and comparison to other parameters to check for convergence.

    Args:
        beta (float): the scale parameter and mean for the exponential
            distribution this also corresponds to the mean, or the
            inverse of the rate of the exponential distribution.
        mu (float): the location parameter and mean for the gaussian
            distribution.
        sigma (float): the scale parameter and the standard deviation
            of the gaussian distribution.
        proportion (float): the proportion of the data that is likelier
            to be gaussian.
    """

    def __init__(self, beta=1.0, mu=0.0, sigma=100.0, proportion=0.5, **kwargs):
        self.beta: float = kwargs.get('beta', beta)
        self.mu: float = kwargs.get('mu', mu)
        self.sigma: float = kwargs.get('sigma', sigma)
        self.proportion: float = kwargs.get('proportion', proportion)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'beta: {self.beta:.5f} | mu: {self.mu:.5f} | ' \
               f'sigma: {self.sigma:.5f} | proportion: {self.proportion:.5f}'

    def as_list(self) -> list:
        """Gets the parameters as a list.

        Returns:
            beta, mu, sigma, and proportion as a list
        """
        return [self.beta, self.mu, self.sigma, self.proportion]

    def max_parameter_difference(self, other) -> float:
        """Get the largest difference in parameters to another GaussianExponentialParameters.

        Compares this object to another GaussianExponentialParameters object parameter by
        parameter and returns the absolute value of the largest difference.

        Args:
            other (GaussianExponentialParameters): the parameters to compare to. This operation
                is symmetric.

        Returns:
            The largest pairwise difference in the parameter list.
        """
        return max([abs(i[0] - i[1]) for i in zip(self.as_list(), other.as_list())])


class GaussianExponentialMixture:

    def __init__(self,
                 data: np.numarray,
                 exp_loc=0.0,
                 max_iterations=100,
                 convergence_tolerance=0.001,
                 **kwargs):

        self.convergence_tolerance: float = convergence_tolerance
        self.data: np.numarray = data
        self._exp_loc: float = exp_loc
        self.parameters = GaussianExponentialParameters(**kwargs)
        self.parameters_updated = GaussianExponentialParameters(**kwargs)
        self.max_iterations: int = max_iterations
        self.expon = stats.expon(loc=self._exp_loc, scale=self.parameters.beta)
        self.norm = stats.norm(loc=self.parameters.mu, scale=self.parameters.sigma)

    def _apply_and_sum(self, func: callable) -> float:
        """Applies a function to the data and returns the sum of the array.

        Args:
            func (callable): a callable with the signature func(val: float) -> float.

        Returns:
            The sum of the data vector after applying func.
        """
        return sum(np.vectorize(func)(self.data))

    def _expectation_is_gaussian(self, val: float) -> float:
        gaussian_density = self.norm.pdf(val)
        exponential_density = self.expon.pdf(val)
        if exponential_density == np.nan:
            return 1
        if gaussian_density == np.nan:
            return 0
        if self.parameters.proportion == 0:
            return 0
        probability_gaussian = gaussian_density * self.parameters.proportion
        probability_exponential = exponential_density * (1 - self.parameters.proportion)
        return probability_gaussian / (probability_gaussian + probability_exponential)

    def _update_beta(self) -> None:
        """Updates the beta parameter (mean/scale) of the exponential distribution.
        """
        self.parameters_updated.beta = \
            self._apply_and_sum(lambda x: (1 - self._expectation_is_gaussian(x)) * x) / \
            self._apply_and_sum(lambda x: (1 - self._expectation_is_gaussian(x)))

    def _update_mu(self) -> None:
        """Updates the mu parameter (mean/location) of the gaussian distribution.
        """
        self.parameters_updated.mu = \
            self._apply_and_sum(lambda x: self._expectation_is_gaussian(x) * x) / \
            self._apply_and_sum(lambda x: self._expectation_is_gaussian(x))

    def _update_sigma(self) -> None:
        """Updates the sigma parameter (standard deviation/scale) of the gaussian distribution.
        """
        sigma_squared = \
            self._apply_and_sum(lambda x: (self._expectation_is_gaussian(x)) * (x - self.parameters_updated.mu) ** 2) / \
            self._apply_and_sum(lambda x: (self._expectation_is_gaussian(x)))
        self.parameters_updated.sigma = math.sqrt(sigma_squared)

    def _update_proportion(self) -> None:
        """Updates the proportion of the data that is likelier gaussian.
        """
        gaussian_total = self._apply_and_sum(lambda x: np.nan_to_num(self.norm.logpdf(x)) >
                                                                 np.nan_to_num(self.expon.logpdf(x)))
        self.parameters_updated.proportion = gaussian_total / len(self.data)

    def _sync_parameters(self) -> None:
        """Copies parameters_updated into parameters.

        This prepares the state of GaussianExponentialMixture for another iteration
        of the EM algorithm with the parameters updated from the previous iteration.
        """
        self.parameters = deepcopy(self.parameters_updated)

    def _update_pdfs(self) -> None:
        """Updates PDFs of normal and exponential with new parameters.

        Since the parameters are stored separately from the PDFs for now, updates
        need to be applied on each iteration.
        """
        self.norm = stats.norm(loc=self.parameters_updated.mu, scale=self.parameters_updated.sigma)
        self.expon = stats.expon(loc=self._exp_loc, scale=self.parameters_updated.beta)

    def _check_parameter_differences(self) -> float:
        """Compares the newly updated parameters to the previous iteration.

        This returns the largest pairwise difference between parameter values for
        use in determining the convergence of EM.
        """
        return self.parameters.max_parameter_difference(self.parameters_updated)

    def _em_step(self) -> None:
        """Performs one EM step on the data and stores the result in updated_parameters.
        """
        self._sync_parameters()
        self._update_beta()
        self._update_mu()
        self._update_sigma()
        self._update_pdfs()
        self._update_proportion()

    def fit(self) -> None:
        """Performs EM steps until convergence criteria are satisfied.
        """
        self._em_step()
        iters = 1
        while iters < self.max_iterations and self._check_parameter_differences() > self.convergence_tolerance:
            self._em_step()
            iters += 1
        self._sync_parameters()

    def pdf(self, val):
        """Evaluates the density of the pdf of the GaussianExponentialMixture.
        """
        return (1 - self.parameters.proportion) * self.expon.pdf(val) + self.parameters.proportion * self.norm.pdf(val)
