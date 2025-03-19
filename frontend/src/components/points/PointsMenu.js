import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCoins, FaHistory, FaGift, FaSpinner } from 'react-icons/fa';
import { useToast } from '../common/Toast';
import { LoadingSpinner, SkeletonLoader } from '../common/Loading';
import './PointsMenu.css';

const PointsMenu = () => {
  const { t } = useTranslation();
  const { addToast } = useToast();
  const [balance, setBalance] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [timeFilter, setTimeFilter] = useState('all');
  const [isRedeeming, setIsRedeeming] = useState(false);

  // Fetch points balance and history
  useEffect(() => {
    const fetchPointsData = async () => {
      try {
        setLoading(true);
        const [balanceRes, historyRes] = await Promise.all([
          fetch('/api/points/balance'),
          fetch(`/api/points/history?time=${timeFilter}`)
        ]);

        if (!balanceRes.ok || !historyRes.ok) {
          throw new Error('Failed to fetch points data');
        }

        const [balanceData, historyData] = await Promise.all([
          balanceRes.json(),
          historyRes.json()
        ]);

        setBalance(balanceData.balance);
        setHistory(historyData.history);
      } catch (err) {
        setError(err.message);
        addToast(err.message, 'error');
      } finally {
        setLoading(false);
      }
    };

    fetchPointsData();
  }, [timeFilter, addToast]);

  // Handle points redemption
  const handleRedeem = async () => {
    if (!selectedOption) return;

    try {
      setIsRedeeming(true);
      const response = await fetch('/api/points/redeem', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          option: selectedOption.id,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to redeem points');
      }

      const data = await response.json();
      setBalance(data.new_balance);
      setHistory(prev => [data.transaction, ...prev]);
      setSelectedOption(null);
      addToast(t('points.redemption.success'), 'success');
    } catch (err) {
      addToast(err.message, 'error');
    } finally {
      setIsRedeeming(false);
    }
  };

  // Redemption options
  const redemptionOptions = [
    {
      id: 'discount_10',
      title: t('points.redemption.discount_10.title'),
      description: t('points.redemption.discount_10.description'),
      cost: 100,
    },
    {
      id: 'discount_20',
      title: t('points.redemption.discount_20.title'),
      description: t('points.redemption.discount_20.description'),
      cost: 200,
    },
    {
      id: 'vip_status',
      title: t('points.redemption.vip_status.title'),
      description: t('points.redemption.vip_status.description'),
      cost: 500,
    },
  ];

  if (loading) {
    return (
      <div className="points-menu">
        <SkeletonLoader type="card" />
        <div className="points-history">
          <SkeletonLoader type="text" count={5} />
        </div>
        <div className="points-redemption">
          <SkeletonLoader type="card" count={3} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="points-error">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="points-menu">
      {/* Points Balance */}
      <div className="points-balance">
        <div className="points-balance-header">
          <h2 className="points-balance-title">
            <FaCoins /> {t('points.balance.title')}
          </h2>
        </div>
        <div className="points-balance-amount">
          {balance} {t('points.balance.points')}
        </div>
        <div className="points-balance-actions">
          <button className="btn btn-light">
            <FaHistory /> {t('points.balance.view_history')}
          </button>
          <button className="btn btn-light">
            <FaGift /> {t('points.balance.redeem')}
          </button>
        </div>
      </div>

      {/* Points History */}
      <div className="points-history">
        <div className="points-history-header">
          <h2 className="points-history-title">
            <FaHistory /> {t('points.history.title')}
          </h2>
          <div className="points-history-filters">
            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value)}
              className="form-select"
            >
              <option value="all">{t('points.history.filters.all')}</option>
              <option value="week">{t('points.history.filters.week')}</option>
              <option value="month">{t('points.history.filters.month')}</option>
              <option value="year">{t('points.history.filters.year')}</option>
            </select>
          </div>
        </div>

        {history.length > 0 ? (
          <table className="points-history-table">
            <thead>
              <tr>
                <th>{t('points.history.table.date')}</th>
                <th>{t('points.history.table.type')}</th>
                <th>{t('points.history.table.amount')}</th>
                <th>{t('points.history.table.description')}</th>
              </tr>
            </thead>
            <tbody>
              {history.map((transaction) => (
                <tr key={transaction.id}>
                  <td>{new Date(transaction.date).toLocaleDateString()}</td>
                  <td>{t(`points.history.types.${transaction.type}`)}</td>
                  <td className={transaction.amount > 0 ? 'text-success' : 'text-danger'}>
                    {transaction.amount > 0 ? '+' : ''}{transaction.amount}
                  </td>
                  <td>{transaction.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="points-empty-state">
            <FaHistory className="points-empty-state-icon" />
            <p className="points-empty-state-text">
              {t('points.history.empty')}
            </p>
          </div>
        )}
      </div>

      {/* Points Redemption */}
      <div className="points-redemption">
        <div className="points-redemption-header">
          <h2 className="points-redemption-title">
            <FaGift /> {t('points.redemption.title')}
          </h2>
          <p className="points-redemption-description">
            {t('points.redemption.description')}
          </p>
        </div>

        <div className="points-redemption-options">
          {redemptionOptions.map((option) => (
            <div
              key={option.id}
              className={`points-option-card ${
                selectedOption?.id === option.id ? 'selected' : ''
              }`}
              onClick={() => setSelectedOption(option)}
            >
              <h3 className="points-option-title">{option.title}</h3>
              <p className="points-option-description">{option.description}</p>
              <div className="points-option-cost">
                {option.cost} {t('points.redemption.points')}
              </div>
            </div>
          ))}
        </div>

        {selectedOption && (
          <div className="points-redemption-form">
            <button
              className="btn btn-primary"
              onClick={handleRedeem}
              disabled={balance < selectedOption.cost || isRedeeming}
            >
              {isRedeeming ? (
                <LoadingSpinner size="small" />
              ) : (
                t('points.redemption.redeem_button')
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PointsMenu; 