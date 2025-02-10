import numpy as np

class DataMgr_Raw_In_Intervals:
    """
    Features implemented in this class:
    * During initialization: Create a 2D array `rawdata_in_intervals`, where each row represents an interval of data.
    """
    def __init__(self, one_interval_data_len, num_intervals):
        """
        Initialize a 2D array where each row represents an interval.
        :param one_interval_data_len: Length of data in each interval.
        :param num_intervals: Total number of intervals to store.
        """
        self.interval_len = one_interval_data_len  # Length of each interval
        self.num_intervals = num_intervals  # Total number of intervals
        self.buf = np.full((num_intervals, one_interval_data_len), np.nan)  # Initialize a 2D array filled with NaN
        self.current_positions = np.zeros(num_intervals, dtype=int)  # Current fill position for each row

    def append(self, newdata):
        """
        Add new data to `rawdata_in_intervals`.
        :param newdata: 1D array or list containing the data to append. A scalar is also accepted.
        """
        # Convert input data to a NumPy 1D array if it is a scalar
        if not isinstance(newdata, np.ndarray):
            data = np.array([newdata])
        elif newdata.ndim == 0:  # If scalar, convert to 1D array
            data = np.array([newdata])
        else:
            data = newdata.flatten()  # Ensure it's a 1D array

        last_row_idx = self.num_intervals - 1  # Index of the last row
        current_pos = self.current_positions[last_row_idx]  # Current filled position in the last row

        # Calculate remaining space in the last row
        remaining_space = self.interval_len - current_pos

        if len(data) <= remaining_space:
            # If the new data fits in the remaining space of the last row
            self.buf[last_row_idx, current_pos:current_pos + len(data)] = data
            self.current_positions[last_row_idx] += len(data)
        else:
            # Fill the remaining space in the last row
            self.buf[last_row_idx, current_pos:] = data[:remaining_space]
            self.current_positions[last_row_idx] = self.interval_len

            # Remaining data
            remaining_data = data[remaining_space:]

            # Calculate the number of shifts (rolls) needed
            num_rolls = (len(remaining_data) - 1) // self.interval_len + 1

            # Roll the buffer and fill the remaining data
            for i in range(num_rolls):
                # Roll the array
                self.buf = np.roll(self.buf, shift=-1, axis=0)
                self.current_positions = np.roll(self.current_positions, shift=-1)

                # Clear the last row after the roll
                self.buf[-1, :] = np.nan
                self.current_positions[-1] = 0

                # Fill the data chunk
                start_idx = i * self.interval_len
                end_idx = min((i + 1) * self.interval_len, len(remaining_data))
                chunk = remaining_data[start_idx:end_idx]

                self.buf[-1, :len(chunk)] = chunk
                self.current_positions[-1] = len(chunk)

        return True

    def find_1st_valid_row(self):
        """
        Find the earliest row that contains data.
        :return: Index of the earliest row with data, or None if no data is found.
        """
        for i, pos in enumerate(self.current_positions):
            if pos > 0:  # Check if the row contains data
                return i
        return None

    def append_new_data_and_return_1st_filled_row(self, data_arrived):
        interval_data = None
        if self.append(data_arrived):
            interval_data =  self.get_1st_filled_row()

        return interval_data

    def find_1st_filled_row_idx(self):
        """
        Find the index of the first fully filled interval row.
        :return: Index of the first fully filled interval, or None if not found.
        """
        for i, pos in enumerate(self.current_positions):
            if pos == self.interval_len:  # Check if the row is fully filled
                return i
        return None

    def delete_1st_filled_row(self):
        """
        Delete the first fully filled interval.
        """
        first_full_interval_idx = self.find_1st_filled_row_idx()
        if first_full_interval_idx is not None:
            self.buf[first_full_interval_idx, :] = np.nan  # Fill with NaN
            self.current_positions[first_full_interval_idx] = 0  # Reset the position

    def get_1st_filled_row(self):
        """
        Retrieve the first fully filled interval.
        :return: A 1D array of the first fully filled interval. Returns None if no complete interval exists.
        """
        first_full_interval_idx = self.find_1st_filled_row_idx()
        if first_full_interval_idx is not None:
            return self.buf[first_full_interval_idx, :]
        return None

class DataMgr_Wave_In_1D:
    def __init__(self, indicator_wave_columns):
        """
        Initialize a 2D array where each row represents an interval.
        :param interval_data_len: Length of data in each interval.
        :param num_intervals: Total number of intervals to store.
        """
        self.buf_len = None
        self.buf = None

        if indicator_wave_columns is not None:
            self.buf_len = indicator_wave_columns
            self.buf = np.full(self.buf_len, np.nan)

    def append(self, data_arrived):
        """
        Generic function for appending data with automatic rolling, used for different buffers.
        :param data_arrived: New data to append (can be scalar or 1D array).
        """
        if not isinstance(data_arrived, np.ndarray):  # If scalar
            data = np.asarray(data_arrived)
            data_len = 1
        elif data_arrived.shape == ():  # Empty array, return directly
            return
        else:  # Non-empty array
            data = data_arrived.flatten()  # Flatten data to 1D array
            data_len = data.shape[0]

        # Roll and fill the buffer
        self.buf = np.roll(self.buf, -data_len)
        self.buf[-data_len:] = data  # Ensure the assigned data is 1D


# Test
if __name__ == "__main__":
    handler = DataMgr_Raw_In_Intervals(one_interval_data_len=25, num_intervals=3)

    # Input data exceeds the length of one interval
    data = np.array([i for i in range(75)])  # Total of 75 data points, 3 intervals in length
    handler.append(data)

    print("Buffer after append:")
    print(handler.buf)
    print("Current Positions:", handler.current_positions)
