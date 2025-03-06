import logging


class Indicator_Globals:
    """
    Why is stream_freq defined here?
    Because each indicator needs to be able to run tests without a GUI, a default frequency parameter is required.
    However, in the GUI, when the user selects a device, the frequency provided by the device may not match the default frequency.

    Considerations:
    - When connecting to a device, the detected frequency could be passed to the indicator as a parameter.
      If we implement it this way, the initialization of the indicator would require a parameter.
      However, this approach increases the cognitive load for developers writing new indicators,
      as they would need to ensure this parameter is handled correctly.

    - In reality, this parameter only needs to be set once during device connection.
      The internal implementation of the indicator framework does not need to be aware of or manage this parameter explicitly.

    Alternative approaches:
    - Hard-code the configuration into the indicator:
        However, if the configuration is incorrect after selecting the device, what should we do?
        Notify the user to adjust the configuration manually.

    - Automatically adjust the configuration:
        This could involve reading and writing configuration files or initializing the configuration class only once.
        However, both approaches would make the code less concise.

    Current solution:
    For now, the parameter is placed here as a configuration setting. It will be checked once when the user selects a device.
    If a better solution is found in the future, we can revisit this design.
    """

    stream_freq = 512  # Default sampling frequency
    logging_level = logging.INFO  # Default logging level
