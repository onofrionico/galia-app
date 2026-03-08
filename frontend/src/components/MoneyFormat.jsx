import React from 'react';
import PropTypes from 'prop-types';
import { formatMoney, formatMoneyWithCurrency } from '../utils/moneyFormat';

const MoneyFormat = ({ amount, currency, className, showCurrency = false }) => {
  const formattedAmount = showCurrency 
    ? formatMoneyWithCurrency(amount, currency)
    : formatMoney(amount);

  return (
    <span className={className}>
      {formattedAmount}
    </span>
  );
};

MoneyFormat.propTypes = {
  amount: PropTypes.oneOfType([
    PropTypes.number,
    PropTypes.string
  ]),
  currency: PropTypes.string,
  className: PropTypes.string,
  showCurrency: PropTypes.bool
};

MoneyFormat.defaultProps = {
  currency: '$',
  showCurrency: false
};

export default MoneyFormat;
