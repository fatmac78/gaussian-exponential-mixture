# Gaussian-Exponential Mixture

## Introduction

Like the name suggests, this package can be used to quickly fit a mixture of an
exponential distribution and a gaussian distribution to some data. This works with
numpy arrays, so you can easily add this to a Jupyter notebook style analysis.

## Motivation

This is a pattern that I have seen in data where there are boundaries to data
and a clear edge distribution forms on the practical lower bound of the global
distribution while a more symmetric population forms somewhere well clear of an edge.

The main motivation for this was for modeling the distribution of a very specific
kind of metric of the form "proportion of elements in a set of groups X that have property Y"
where X is of high cardinality (more than 100 groups) and Y is noisy, but will have two distinct
populations.

Unfortunately I cannot show the real context that this analysis was done in, so a very contrived example
(that may or may not hold up against real data) will have to be used as an example.

Say the groups X are cities in the world (say the most populous 1000, so we have a manageable set),
the elements of interest are people, and the property Y we are measuring is whether or not someone
who lives in that city has been to been to Italy. For each city we have a number between 0 and 1
indicating the proportion of people in that city that have been to Italy. You can imagine that two distributions
might appear, one for cities that are close to Italy or in the EU where 10%-20% of residents may have made a trip
Italy before, and a second much larger edge distribution near zero for cities outside of Europe where only
a few residents have ever visited Italy. It is worth the extra effort useful to parameterize
in this way if you want to make comparisons between different properties of interest (e.g. comparing
the distribution for France to Italy), since the four parameters in the model are intuitive and very
descriptive of the underlying distribution.

## Installing

This requires python 3.6 +

```shell script
git clone https://github.com/ethanwh/gaussian-exponential-mixture.git
cd gaussian-exponential-mixture
pip install .
```

## Usage
```python
import numpy
from gaussian_exponential_mixture import GaussianExponentialMixture

beta, mu, sigma = 1, 10, 1

exponential_data = numpy.random.exponential(scale=beta, size=500)
gaussian_data = numpy.random.normal(loc=mu, scale=sigma, size=500)
mixed_data = numpy.append(exponential_data, gaussian_data)
mix = GaussianExponentialMixture(mixed_data)
mix.fit()

print(mix.parameters)
```

```
beta: 1.02511 | mu: 9.97145 | sigma: 1.04869 | proportion: 0.50000
```

To see the results next to the data you can plot the fit distribution.

```python
from matplotlib import pyplot as plt
x = numpy.arange(20, step=0.2)
plt.plot(x, mix.pdf(x))
plt.hist(mixed_data, density=True, bins=50)
plt.show()
```
![image](https://user-images.githubusercontent.com/19494792/67649025-ca927e00-f90d-11e9-8658-068148e893a6.png)
