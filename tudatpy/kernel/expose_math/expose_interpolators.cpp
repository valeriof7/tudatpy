/*    Copyright (c) 2010-2018, Delft University of Technology
 *    All rights reserved
 *
 *    This file is part of the Tudat. Redistribution and use in source and
 *    binary forms, with or without modification, are permitted exclusively
 *    under the terms of the Modified BSD license. You should have received
 *    a copy of the license with this file. If not, please or visit:
 *    http://tudat.tudelft.nl/LICENSE.
 */

#include "expose_interpolators.h"

#include <pybind11/pybind11.h>

#include <pybind11/eigen.h>
#include <pybind11/functional.h>
#include <type_traits>
#include <unsupported/Eigen/CXX11/Tensor>

#include <pybind11/stl.h>
#include <variant>

namespace py = pybind11;

namespace ti = tudat::interpolators;

namespace tudatpy {

namespace prototype {

template<typename X, typename Y>
std::function<std::map<X, Y>(std::vector<X>)> interp1d(std::map<X, Y> &stateMap,
                                                       const std::string &kind = "linear",
                                                       const int &interpolateOrder = 8) {

  std::shared_ptr<ti::InterpolatorSettings> interpolatorSettings;
  if (kind == "lagrange") {
    interpolatorSettings = std::make_shared<ti::LagrangeInterpolatorSettings>(interpolateOrder);
  } else if (kind == "linear") {
    interpolatorSettings = std::make_shared<ti::InterpolatorSettings>(ti::linear_interpolator);
  } else if (kind == "piecewise_constant") {
    interpolatorSettings = std::make_shared<ti::InterpolatorSettings>(ti::piecewise_constant_interpolator);
  } else if (kind == "cubic_spline") {
    interpolatorSettings = std::make_shared<ti::InterpolatorSettings>(ti::cubic_spline_interpolator);
  } else if (kind == "hermite_spline") {
    interpolatorSettings = std::make_shared<ti::InterpolatorSettings>(ti::hermite_spline_interpolator);
  } else {
    throw std::invalid_argument("Argument for 'kind' is invalid.");
  }
  std::shared_ptr<ti::OneDimensionalInterpolator<X, Y>> interpolator =
      ti::createOneDimensionalInterpolator(stateMap, interpolatorSettings);

  return [=](std::vector<X> x) {
    std::map<X, Y> interpolated;
    for (auto &x_i : x) {
      interpolated.insert({x_i, interpolator->interpolate(x_i)});
    }
    return interpolated;
  };
}

}// namespace prototype

void expose_interpolators(py::module &m) {

  py::class_<
      ti::OneDimensionalInterpolator<double, Eigen::VectorXd>,
      std::shared_ptr<ti::OneDimensionalInterpolator<double, Eigen::VectorXd>>>
      OneDimensionalInterpolator(m, "OneDimensionalInterpolator");

  py::class_<ti::CubicSplineInterpolator<double, Eigen::VectorXd>,
             std::shared_ptr<ti::CubicSplineInterpolator<double, Eigen::VectorXd>>,
             ti::OneDimensionalInterpolator<double, Eigen::VectorXd>>
      CubicSplineInterpolator(m, "CubicSplineInterpolator");

  py::class_<ti::HermiteCubicSplineInterpolator<double, Eigen::VectorXd>,
             std::shared_ptr<ti::HermiteCubicSplineInterpolator<double, Eigen::VectorXd>>,
             ti::OneDimensionalInterpolator<double, Eigen::VectorXd>>
      HermiteCubicSplineInterpolator(m, "HermiteCubicSplineInterpolator");

  py::class_<ti::LagrangeInterpolator<double, Eigen::VectorXd>,
             std::shared_ptr<ti::LagrangeInterpolator<double, Eigen::VectorXd>>,
             ti::OneDimensionalInterpolator<double, Eigen::VectorXd>>
      LagrangeInterpolator(m, "LagrangeInterpolator");

  py::class_<ti::LinearInterpolator<double, Eigen::VectorXd>,
             std::shared_ptr<ti::LinearInterpolator<double, Eigen::VectorXd>>,
             ti::OneDimensionalInterpolator<double, Eigen::VectorXd>>
      LinearInterpolator(m, "LinearInterpolator");

  m.def("interp1d",
        py::overload_cast<
            std::map<double, Eigen::VectorXd> &,
            const std::string &,
            const int &>(&prototype::interp1d<double, Eigen::VectorXd>),
        py::arg("variable_map"),
        py::arg("kind") = "linear",
        py::arg("order") = 8);

  m.def("interp1d",
        py::overload_cast<
            std::map<double, Eigen::MatrixXd> &,
            const std::string &,
            const int &>(&prototype::interp1d<double, Eigen::MatrixXd>),
        py::arg("variable_map"),
        py::arg("kind") = "linear",
        py::arg("order") = 8);

  py::enum_<ti::BoundaryInterpolationType>(m, "BoundaryInterpolationType")
      .value("throw_exception_at_boundary", ti::BoundaryInterpolationType::throw_exception_at_boundary)
      .value("use_boundary_value", ti::BoundaryInterpolationType::use_boundary_value)
      .value("use_boundary_value_with_warning", ti::BoundaryInterpolationType::use_boundary_value_with_warning)
      .value("extrapolate_at_boundary", ti::BoundaryInterpolationType::extrapolate_at_boundary)
      .value("extrapolate_at_boundary_with_warning", ti::BoundaryInterpolationType::extrapolate_at_boundary_with_warning)
      .value("use_default_value", ti::BoundaryInterpolationType::use_default_value)
      .value("use_default_value_with_warning", ti::BoundaryInterpolationType::use_default_value_with_warning)
      .export_values();

  py::enum_<ti::AvailableLookupScheme>(m, "AvailableLookupScheme")
      .value("hunting_algorithm", ti::AvailableLookupScheme::huntingAlgorithm)
      .value("binary_search", ti::AvailableLookupScheme::binarySearch)
      .export_values();

  py::enum_<ti::LagrangeInterpolatorBoundaryHandling>(m, "LagrangeInterpolatorBoundaryHandling")
      .value("lagrange_cubic_spline_boundary_interpolation", ti::LagrangeInterpolatorBoundaryHandling::lagrange_no_boundary_interpolation)
      .value("lagrange_no_boundary_interpolation", ti::LagrangeInterpolatorBoundaryHandling::lagrange_no_boundary_interpolation)
      .export_values();

  py::class_<ti::InterpolatorSettings,
             std::shared_ptr<ti::InterpolatorSettings>>
      InterpolatorSettings(m, "InterpolatorSettings");

  py::class_<
      ti::LagrangeInterpolatorSettings,
      std::shared_ptr<ti::LagrangeInterpolatorSettings>,
      ti::InterpolatorSettings>(m,
                                "LagrangeInterpolatorSettings",
                                "Class for providing settings to creating a Lagrange interpolator.")
      .def(py::init<
               const int,
               const bool,
               const ti::AvailableLookupScheme,
               const ti::LagrangeInterpolatorBoundaryHandling,
               const ti::BoundaryInterpolationType>(),
           py::arg("interpolate_order"),
           py::arg("use_long_double_time_step") = 0,
           py::arg("selected_lookup_scheme") = ti::huntingAlgorithm,
           py::arg("lagrange_boundary_handling") = ti::lagrange_cubic_spline_boundary_interpolation,
           py::arg("boundary_handling") = ti::extrapolate_at_boundary);
};

}// namespace tudatpy
