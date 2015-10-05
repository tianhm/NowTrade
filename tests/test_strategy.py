import unittest
import datetime
import numpy as np
from testing_data import DummyDataConnection
from nowtrade import symbol_list, data_connection, dataset, technical_indicator, \
                     criteria, criteria_group, trading_profile, trading_amount, \
                     trading_fee, report, strategy
from nowtrade.action import Long, Short, LongExit, ShortExit, SHORT_EXIT

class TestStrategy(unittest.TestCase):
    def setUp(self):
        self.dc = DummyDataConnection()
        self.sl = symbol_list.SymbolList(['MSFT'])
        self.symbol = self.sl.get('msft')
        self.d = dataset.Dataset(self.sl, self.dc, None, None, 0)
        self.d.load_data()

    def test_simple_long_strategy(self):
        enter_crit = criteria.Above(self.symbol.close, 25.88)
        exit_crit = criteria.BarsSinceLong(self.symbol, 2)
        enter_crit_group = criteria_group.CriteriaGroup([enter_crit], Long(), self.symbol)
        exit_crit_group = criteria_group.CriteriaGroup([exit_crit], LongExit(), self.symbol)
        tp = trading_profile.TradingProfile(10000, trading_amount.StaticAmount(5000), trading_fee.StaticFee(0))
        strat = strategy.Strategy(self.d, [enter_crit_group, exit_crit_group], tp)
        repr_string = 'Strategy(dataset=Dataset(symbol_list=[MSFT], data_connection=DummyDataConnection(), start_datetime=None, end_datetime=None, periods=0, granularity=None), criteria_groups=[CriteriaGroup(criteria_list=[Above_MSFT_Close_25.88_1, Not_InMarket(symbol=MSFT)], action=long, symbol=MSFT), CriteriaGroup(criteria_list=[BarsSinceLong_MSFT_2_None, IsLong_MSFT], action=longexit, symbol=MSFT)], trading_profile=TradingProfile(capital=10000, trading_amount=StaticAmount(amount=5000, round_up=False), trading_fee=StaticFee(fee=0), slippage=0.0)'
        self.assertEquals(strat.__repr__(), repr_string)
        strat.simulate()
        report_overview = strat.report.overview()
        self.assertAlmostEqual(strat.realtime_data_frame.iloc[4]['PL_MSFT'], report_overview['net_profit'])
        self.assertTrue(np.isnan(strat.realtime_data_frame.iloc[0]['CHANGE_PERCENT_MSFT']))
        self.assertTrue(np.isnan(strat.realtime_data_frame.iloc[5]['CHANGE_VALUE_MSFT']))
        self.assertEqual(strat.realtime_data_frame.iloc[0]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['ACTIONS_MSFT'], 1)
        self.assertEqual(strat.realtime_data_frame.iloc[2]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[3]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[4]['ACTIONS_MSFT'], -1)
        self.assertEqual(strat.realtime_data_frame.iloc[5]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[0]['STATUS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['STATUS_MSFT'], 1)
        self.assertEqual(strat.realtime_data_frame.iloc[2]['STATUS_MSFT'], 1)
        self.assertEqual(strat.realtime_data_frame.iloc[3]['STATUS_MSFT'], 1)
        self.assertEqual(strat.realtime_data_frame.iloc[4]['STATUS_MSFT'], 0)
        self.assertEqual(report_overview['trades'], 1)
        self.assertEqual(report_overview['winning_trades'], 0)
        self.assertEqual(report_overview['losing_trades'], 1)
        self.assertEqual(report_overview['lacking_capital'], 0)
        self.assertEqual(report_overview['gross_profit'], 0)
        self.assertEqual(report_overview['gross_loss'], report_overview['net_profit'])
        self.assertEqual(report_overview['ongoing_trades'], 0)
        self.assertEqual(report_overview['average_trading_amount'], 5003.5199999999995)
        self.assertEqual(report_overview['profitability'], 0)

    def test_simple_short_strategy(self):
        enter_crit = criteria.Above(self.symbol.close, 25.88)
        exit_crit = criteria.BarsSinceShort(self.symbol, 2)
        enter_crit_group = criteria_group.CriteriaGroup([enter_crit], Short(), self.symbol)
        exit_crit_group = criteria_group.CriteriaGroup([exit_crit], ShortExit(), self.symbol)
        tp = trading_profile.TradingProfile(10000, trading_amount.StaticAmount(5000), trading_fee.StaticFee(0))
        strat = strategy.Strategy(self.d, [enter_crit_group, exit_crit_group], tp)
        strat.simulate()
        report_overview = strat.report.overview()
        self.assertAlmostEqual(strat.realtime_data_frame.iloc[4]['PL_MSFT'], report_overview['net_profit'])
        self.assertTrue(np.isnan(strat.realtime_data_frame.iloc[0]['CHANGE_PERCENT_MSFT']))
        self.assertTrue(np.isnan(strat.realtime_data_frame.iloc[5]['CHANGE_VALUE_MSFT']))
        self.assertEqual(strat.realtime_data_frame.iloc[0]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['ACTIONS_MSFT'], 2)
        self.assertEqual(strat.realtime_data_frame.iloc[2]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[3]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[4]['ACTIONS_MSFT'], -2)
        self.assertEqual(strat.realtime_data_frame.iloc[5]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[0]['STATUS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['STATUS_MSFT'], -1)
        self.assertEqual(strat.realtime_data_frame.iloc[2]['STATUS_MSFT'], -1)
        self.assertEqual(strat.realtime_data_frame.iloc[3]['STATUS_MSFT'], -1)
        self.assertEqual(strat.realtime_data_frame.iloc[4]['STATUS_MSFT'], 0)
        self.assertEqual(report_overview['trades'], 1)
        self.assertEqual(report_overview['winning_trades'], 1)
        self.assertEqual(report_overview['losing_trades'], 0)
        self.assertEqual(report_overview['lacking_capital'], 0)
        self.assertEqual(report_overview['gross_loss'], 0)
        self.assertEqual(report_overview['gross_profit'], report_overview['net_profit'])
        self.assertEqual(report_overview['ongoing_trades'], 0)
        self.assertEqual(report_overview['average_trading_amount'], 5003.5199999999995)
        self.assertEqual(report_overview['profitability'], 100.00)

    def test_stop_loss_strategy(self):
        enter_crit = criteria.Above(self.symbol.close, 25.88)
        exit_crit = criteria.StopLoss(self.symbol, -0.8)
        enter_crit_group = criteria_group.CriteriaGroup([enter_crit], Long(), self.symbol)
        exit_crit_group = criteria_group.CriteriaGroup([exit_crit], LongExit(), self.symbol)
        tp = trading_profile.TradingProfile(10000, trading_amount.StaticAmount(5000), trading_fee.StaticFee(0))
        strat = strategy.Strategy(self.d, [enter_crit_group, exit_crit_group], tp)
        strat.simulate()
        report_overview = strat.report.overview()
        self.assertAlmostEqual(strat.realtime_data_frame.iloc[-2]['PL_MSFT'], report_overview['net_profit'])
        self.assertTrue(np.isnan(strat.realtime_data_frame.iloc[0]['CHANGE_PERCENT_MSFT']))
        self.assertTrue(np.isnan(strat.realtime_data_frame.iloc[-1]['CHANGE_VALUE_MSFT']))
        self.assertEqual(strat.realtime_data_frame.iloc[0]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['ACTIONS_MSFT'], 1)
        self.assertEqual(strat.realtime_data_frame.iloc[-2]['ACTIONS_MSFT'], -1)
        self.assertEqual(strat.realtime_data_frame.iloc[-1]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[0]['STATUS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['STATUS_MSFT'], 1)
        self.assertEqual(strat.realtime_data_frame.iloc[-3]['STATUS_MSFT'], 1)
        self.assertEqual(strat.realtime_data_frame.iloc[-2]['STATUS_MSFT'], 0)
        self.assertEqual(report_overview['trades'], 1)
        self.assertEqual(report_overview['winning_trades'], 0)
        self.assertEqual(report_overview['losing_trades'], 1)
        self.assertEqual(report_overview['lacking_capital'], 0)
        self.assertEqual(report_overview['gross_loss'], report_overview['net_profit'])
        self.assertEqual(report_overview['ongoing_trades'], 0)
        self.assertEqual(report_overview['average_trading_amount'], 5003.5199999999995)
        self.assertEqual(report_overview['profitability'], 0.0)

    def test_trailing_stop_long_strategy(self):
        enter_crit = criteria.Above(self.symbol.close, 25.88)
        exit_crit = criteria.TrailingStop(self.symbol, -0.2)
        enter_crit_group = criteria_group.CriteriaGroup([enter_crit], Long(), self.symbol)
        exit_crit_group = criteria_group.CriteriaGroup([exit_crit], LongExit(), self.symbol)
        tp = trading_profile.TradingProfile(10000, trading_amount.StaticAmount(5000), trading_fee.StaticFee(0))
        strat = strategy.Strategy(self.d, [enter_crit_group, exit_crit_group], tp)
        strat.simulate()
        report_overview = strat.report.overview()
        self.assertTrue(np.isnan(strat.realtime_data_frame.iloc[0]['CHANGE_PERCENT_MSFT']))
        self.assertEqual(strat.realtime_data_frame.iloc[-5]['CHANGE_VALUE_MSFT'], -0.26999999999999957)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['CHANGE_VALUE_MSFT'], 0.40000000000000213)
        self.assertEqual(strat.realtime_data_frame.iloc[2]['PL_MSFT'], 153.60000000000014)
        self.assertEqual(strat.realtime_data_frame.iloc[0]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['ACTIONS_MSFT'], 1)
        self.assertEqual(strat.realtime_data_frame.iloc[2]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[4]['ACTIONS_MSFT'], -1)
        self.assertEqual(strat.realtime_data_frame.iloc[5]['ACTIONS_MSFT'], 0)

    def test_trailing_stop_short_strategy(self):
        enter_crit = criteria.Above(self.symbol.close, 25.88)
        exit_crit = criteria.TrailingStop(self.symbol, -0.2)
        enter_crit_group = criteria_group.CriteriaGroup([enter_crit], Long(), self.symbol)
        exit_crit_group = criteria_group.CriteriaGroup([exit_crit], LongExit(), self.symbol)
        tp = trading_profile.TradingProfile(10000, trading_amount.StaticAmount(5000), trading_fee.StaticFee(0))
        strat = strategy.Strategy(self.d, [enter_crit_group, exit_crit_group], tp)
        strat.simulate()
        self.assertTrue(np.isnan(strat.realtime_data_frame.iloc[0]['CHANGE_PERCENT_MSFT']))
        self.assertTrue(np.isnan(strat.realtime_data_frame.iloc[-3]['CHANGE_VALUE_MSFT']))
        self.assertEqual(strat.realtime_data_frame.iloc[-4]['CHANGE_VALUE_MSFT'], -0.23999999999999844)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['CHANGE_VALUE_MSFT'], 0.40000000000000213)
        self.assertEqual(strat.realtime_data_frame.iloc[2]['PL_MSFT'], 153.60000000000014)
        self.assertEqual(strat.realtime_data_frame.iloc[3]['CHANGE_PERCENT_MSFT'], -0.01036070606293168)
        self.assertEqual(strat.realtime_data_frame.iloc[0]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[1]['ACTIONS_MSFT'], 1)
        self.assertEqual(strat.realtime_data_frame.iloc[2]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[3]['ACTIONS_MSFT'], 0)
        self.assertEqual(strat.realtime_data_frame.iloc[4]['ACTIONS_MSFT'], -1)

    def test_upcoming_action(self):
        enter_crit = criteria.Above(self.symbol.close, 25.88)
        exit_crit = criteria.Equals(self.symbol.close, 25.00)
        enter_crit_group = criteria_group.CriteriaGroup([enter_crit], Short(), self.symbol)
        exit_crit_group = criteria_group.CriteriaGroup([exit_crit], ShortExit(), self.symbol)
        tp = trading_profile.TradingProfile(10000, trading_amount.StaticAmount(5000), trading_fee.StaticFee(0))
        strat = strategy.Strategy(self.d, [enter_crit_group, exit_crit_group], tp)
        strat.simulate()
        next_action = strat.get_next_action()[self.symbol]
        self.assertTrue(self.symbol in strat.upcoming_actions)
        self.assertEqual(strat.upcoming_actions[self.symbol], SHORT_EXIT)
        self.assertEqual(next_action['estimated_money_required'], 5000.8699999999999)
        self.assertEqual(next_action['estimated_enter_value'], 25.129999999999999)
        self.assertEqual(next_action['action_name'], 'SHORT_EXIT')
        self.assertEqual(next_action['estimated_shares'], 199.0)
        self.assertEqual(next_action['action'], SHORT_EXIT)
        self.assertEqual(next_action['enter_on'], 'OPEN')

if __name__ == "__main__":
    unittest.main()
