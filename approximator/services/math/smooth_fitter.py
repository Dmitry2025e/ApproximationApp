import numpy as np

class SplineFitter:
    """
    Математическое ядро для сглаженной аппроксимации с возможностью сшивки сегментов.
    continuity: 0 — только C0 (по значению), 1 — C0+C1 (значение+производная), 2 — C0+C1+C2 (значение+1-я+2-я производная)
    """
    @staticmethod
    def get_poly_and_deriv_matrix(x, degree):
        x_col = x.reshape(-1, 1)
        poly_matrix = np.power(x_col, np.arange(degree, -1, -1))
        with np.errstate(divide='ignore', invalid='ignore'):
            if degree > 0:
                powers = np.arange(degree, -1, -1)
                deriv_matrix = powers * np.power(x_col, powers - 1)
                deriv_matrix[np.isnan(deriv_matrix)] = 0
                deriv_matrix[:, -1] = 0
            else:
                deriv_matrix = np.zeros_like(poly_matrix)
        return poly_matrix, deriv_matrix

    def fit(self, segments, data, continuity=1):
        if not segments:
            return []
        coeffs_per_segment = [seg.poly_degree + 1 for seg in segments]
        total_coeffs = sum(coeffs_per_segment)
        coeff_indices = np.cumsum([0] + coeffs_per_segment)
        data_eqs, b_data = [], []
        for i, seg in enumerate(segments):
            mask = (data[:, 0] >= seg.x_start) & (data[:, 0] <= seg.x_end)
            x_seg, y_seg = data[mask, 0], data[mask, 1]
            if len(x_seg) > 0:
                poly_matrix, _ = self.get_poly_and_deriv_matrix(x_seg, seg.poly_degree)
                row = np.zeros((len(x_seg), total_coeffs))
                start_col, end_col = coeff_indices[i], coeff_indices[i+1]
                row[:, start_col:end_col] = poly_matrix
                data_eqs.append(row)
                b_data.append(y_seg)
        if not data_eqs:
            return []
        A_data, b_data = np.vstack(data_eqs), np.concatenate(b_data)
        constraint_eqs = []
        if len(segments) > 1:
            for i in range(len(segments) - 1):
                seg1, seg2 = segments[i], segments[i+1]
                t = seg1.x_end
                p1_matrix, d1_matrix = self.get_poly_and_deriv_matrix(np.array([t]), seg1.poly_degree)
                p2_matrix, d2_matrix = self.get_poly_and_deriv_matrix(np.array([t]), seg2.poly_degree)
                c0_row = np.zeros(total_coeffs)
                c0_row[coeff_indices[i]:coeff_indices[i+1]] = p1_matrix
                c0_row[coeff_indices[i+1]:coeff_indices[i+2]] = -p2_matrix
                constraint_eqs.append(c0_row)
                if continuity >= 1:
                    c1_row = np.zeros(total_coeffs)
                    c1_row[coeff_indices[i]:coeff_indices[i+1]] = d1_matrix
                    c1_row[coeff_indices[i+1]:coeff_indices[i+2]] = -d2_matrix
                    constraint_eqs.append(c1_row)
                if continuity >= 2:
                    def get_second_deriv_matrix(x, degree):
                        x_col = x.reshape(-1, 1)
                        if degree > 1:
                            powers = np.arange(degree, -1, -1)
                            second_deriv = powers * (powers - 1) * np.power(x_col, powers - 2)
                            second_deriv[np.isnan(second_deriv)] = 0
                            second_deriv[:, -1] = 0
                            if degree > 0:
                                second_deriv[:, -2] = 0
                        else:
                            second_deriv = np.zeros_like(x_col)
                        return second_deriv
                    d2_1 = get_second_deriv_matrix(np.array([t]), seg1.poly_degree)
                    d2_2 = get_second_deriv_matrix(np.array([t]), seg2.poly_degree)
                    c2_row = np.zeros(total_coeffs)
                    c2_row[coeff_indices[i]:coeff_indices[i+1]] = d2_1
                    c2_row[coeff_indices[i+1]:coeff_indices[i+2]] = -d2_2
                    constraint_eqs.append(c2_row)
        A_constraint = np.array(constraint_eqs)
        W = 1000
        if A_constraint.size > 0:
            b_constraint = np.zeros(len(A_constraint))
            A = np.vstack([A_data, A_constraint * W])
            b = np.concatenate([b_data, b_constraint * W])
        else:
            A = A_data
            b = b_data
        try:
            coeffs_flat, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
            return [np.poly1d(coeffs_flat[coeff_indices[i]:coeff_indices[i+1]]) for i in range(len(segments))]
        except np.linalg.LinAlgError:
            return []
