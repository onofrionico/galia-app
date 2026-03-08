import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { formatMoney, parseMoney } from '../utils/moneyFormat';

const MoneyInput = ({ 
  value, 
  onChange, 
  className, 
  placeholder = '0,00',
  required = false,
  disabled = false,
  name,
  id
}) => {
  const [displayValue, setDisplayValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => {
    if (!isFocused) {
      if (value === '' || value === null || value === undefined) {
        setDisplayValue('');
      } else {
        setDisplayValue(formatMoney(value));
      }
    }
  }, [value, isFocused]);

  const handleFocus = (e) => {
    setIsFocused(true);
    const numericValue = parseMoney(displayValue);
    if (numericValue === 0) {
      setDisplayValue('');
    }
  };

  const handleBlur = (e) => {
    setIsFocused(false);
    const numericValue = parseMoney(displayValue);
    if (onChange) {
      onChange(numericValue);
    }
    setDisplayValue(formatMoney(numericValue));
  };

  const handleChange = (e) => {
    const inputValue = e.target.value;
    setDisplayValue(inputValue);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.target.blur();
    }
  };

  return (
    <input
      type="text"
      id={id}
      name={name}
      value={displayValue}
      onChange={handleChange}
      onFocus={handleFocus}
      onBlur={handleBlur}
      onKeyDown={handleKeyDown}
      className={className}
      placeholder={placeholder}
      required={required}
      disabled={disabled}
      inputMode="decimal"
    />
  );
};

MoneyInput.propTypes = {
  value: PropTypes.oneOfType([
    PropTypes.number,
    PropTypes.string
  ]),
  onChange: PropTypes.func,
  className: PropTypes.string,
  placeholder: PropTypes.string,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  name: PropTypes.string,
  id: PropTypes.string
};

export default MoneyInput;
