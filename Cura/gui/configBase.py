from __future__ import division
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx, wx.lib.stattext, types
from wx.lib.agw import floatspin

from Cura.util import validators
from Cura.util import profile
from Cura.gui import configWizard

class configPanelBase(wx.Panel):
	"A base class for configuration dialogs. Handles creation of settings, and popups"
	def __init__(self, parent, changeCallback = None):
		super(configPanelBase, self).__init__(parent)
		
		self.settingControlList = []

		self._callback = changeCallback
	
	def CreateConfigTab(self, nb, name):
		leftConfigPanel, rightConfigPanel, configPanel = self.CreateConfigPanel(nb)
		nb.AddPage(configPanel, name)
		return leftConfigPanel, rightConfigPanel
	
	def CreateConfigPanel(self, parent):
		configPanel = wx.Panel(parent)
		leftConfigPanel = wx.Panel(configPanel)
		rightConfigPanel = wx.Panel(configPanel)

		sizer = wx.GridBagSizer(2, 2)
		leftConfigPanel.SetSizer(sizer)
		sizer = wx.GridBagSizer(2, 2)
		rightConfigPanel.SetSizer(sizer)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		configPanel.SetSizer(sizer)
		sizer.Add(leftConfigPanel, border=35, flag=wx.RIGHT)
		sizer.Add(rightConfigPanel)
		leftConfigPanel.main = self
		rightConfigPanel.main = self
		return leftConfigPanel, rightConfigPanel, configPanel

	def CreateDynamicConfigTab(self, nb, name):
		configPanel = wx.lib.scrolledpanel.ScrolledPanel(nb)	
		#configPanel = wx.Panel(nb);
		leftConfigPanel = wx.Panel(configPanel)
		rightConfigPanel = wx.Panel(configPanel)

		sizer = wx.GridBagSizer(2, 2)
		leftConfigPanel.SetSizer(sizer)
		#sizer.AddGrowableCol(1)

		sizer = wx.GridBagSizer(2, 2)
		rightConfigPanel.SetSizer(sizer)
		#sizer.AddGrowableCol(1)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(leftConfigPanel, proportion=1, border=35, flag=wx.EXPAND)
		sizer.Add(rightConfigPanel, proportion=1, flag=wx.EXPAND)
		configPanel.SetSizer(sizer)

		configPanel.SetAutoLayout(1)
		configPanel.SetupScrolling(scroll_x=False, scroll_y=True)

		leftConfigPanel.main = self
		rightConfigPanel.main = self

		configPanel.leftPanel = leftConfigPanel
		configPanel.rightPanel = rightConfigPanel

		nb.AddPage(configPanel, name)

		return leftConfigPanel, rightConfigPanel, configPanel
    
	def updateProfileToControls(self):
		"Update the configuration wx controls to show the new configuration settings"
		for setting in self.settingControlList:
			setting.SetValue(setting.setting.getValue())
		self.Update()

	def _validate(self):
		for setting in self.settingControlList:
			setting._validate()
		if self._callback is not None:
			self._callback()

	def getLabelColumnWidth(self, panel):
		maxWidth = 0
		for child in panel.GetChildren():
			if isinstance(child, wx.lib.stattext.GenStaticText):
				maxWidth = max(maxWidth, child.GetSize()[0])
		return maxWidth
	
	def setLabelColumnWidth(self, panel, width):
		for child in panel.GetChildren():
			if isinstance(child, wx.lib.stattext.GenStaticText):
				size = child.GetSize()
				size[0] = width
				child.SetBestSize(size)
	
class TitleRow(object):
	def __init__(self, panel, name):
		"Add a title row to the configuration panel"
		sizer = panel.GetSizer()
		x = sizer.GetRows()
		self.title = wx.StaticText(panel, -1, name.replace('&', '&&'))
		self.title.SetFont(wx.Font(wx.SystemSettings.GetFont(wx.SYS_ANSI_VAR_FONT).GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
		sizer.Add(self.title, (x,0), (1,3), flag=wx.EXPAND|wx.TOP|wx.LEFT, border=10)
		sizer.Add(wx.StaticLine(panel), (x+1,0), (1,4), flag=wx.EXPAND|wx.LEFT,border=10)
		sizer.SetRows(x + 2)

class SettingRow(object):
	def __init__(self, panel, configName, valueOverride = None, index = None):
		"Add a setting to the configuration panel"
		sizer = panel.GetSizer()
		x = sizer.GetRows()
		y = 0
		flag = 0
		has_expert_settings = False

		self.setting = profile.settingsDictionary[configName]
		self.settingIndex = index
		self.validationMsg = ''
		self.panel = panel

		self.label = wx.lib.stattext.GenStaticText(panel, -1, self.setting.getLabel())
		self.label.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)

		#if self.setting.getType() is types.FloatType and False:
		#	digits = 0
		#	while 1 / pow(10, digits) > defaultValue:
		#		digits += 1
		#	self.ctrl = floatspin.FloatSpin(panel, -1, value=float(getSettingFunc(configName)), increment=defaultValue, digits=digits, min_val=0.0)
		#	self.ctrl.Bind(floatspin.EVT_FLOATSPIN, self.OnSettingChange)
		#	flag = wx.EXPAND
		if self.setting.getType() is types.BooleanType:
			self.ctrl = wx.CheckBox(panel, -1, style=wx.ALIGN_RIGHT)
			self.SetValue(self.setting.getValue(self.settingIndex))
			self.ctrl.Bind(wx.EVT_CHECKBOX, self.OnSettingChange)
		elif valueOverride is not None and valueOverride is wx.Colour:
			self.ctrl = wx.ColourPickerCtrl(panel, -1)
			self.SetValue(self.setting.getValue(self.settingIndex))
			self.ctrl.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnSettingChange)
		elif type(self.setting.getType()) is list or valueOverride is not None:
			value = self.setting.getValue(self.settingIndex)
			choices = self.setting.getType()
			if valueOverride is not None:
				choices = valueOverride
			choices = choices[:]
			self._englishChoices = choices[:]
			if value not in choices and len(choices) > 0:
				value = choices[0]
			for n in xrange(0, len(choices)):
				choices[n] = _(choices[n])
			value = _(value)
			self.ctrl = wx.ComboBox(panel, -1, value, choices=choices, style=wx.CB_DROPDOWN|wx.CB_READONLY)
			self.ctrl.Bind(wx.EVT_COMBOBOX, self.OnSettingChange)
			self.ctrl.Bind(wx.EVT_LEFT_DOWN, self.OnMouseExit)
			flag = wx.EXPAND
		else:
			self.ctrl = wx.TextCtrl(panel, -1, self.setting.getValue(self.settingIndex))
			self.ctrl.Bind(wx.EVT_TEXT, self.OnSettingChange)
			flag = wx.EXPAND

		self.ctrl.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
		sizer.Add(self.label, (x,y), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT,border=10)
		sizer.Add(self.ctrl, (x,y+1), flag=wx.ALIGN_CENTER_VERTICAL|flag)
		if self.setting.getExpertSubCategory() is not None:
			self._expert_button = wx.Button(panel, -1, '...', style=wx.BU_EXACTFIT)
			self._expert_button.SetFont(wx.Font(wx.SystemSettings.GetFont(wx.SYS_ANSI_VAR_FONT).GetPointSize() * 0.8, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.FONTWEIGHT_NORMAL))
			self._expert_button.Bind(wx.EVT_BUTTON, self.OnExpertOpen)
			sizer.Add(self._expert_button, (x,y+2), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.SetRows(x+1)

		self.ctrl.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
		if isinstance(self.ctrl, floatspin.FloatSpin):
			self.ctrl.GetTextCtrl().Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
			self.defaultBGColour = self.ctrl.GetTextCtrl().GetBackgroundColour()
		else:
			self.defaultBGColour = self.ctrl.GetBackgroundColour()
		
		panel.main.settingControlList.append(self)

	def OnMouseEnter(self, e):
		self.label.SetToolTipString(self.setting.getTooltip())
		self.ctrl.SetToolTipString(self.setting.getTooltip())

	def OnMouseExit(self, e):
		self.label.SetToolTipString('')
		self.ctrl.SetToolTipString('')
		e.Skip()

	def OnSettingChange(self, e):
		self.setting.setValue(self.GetValue(), self.settingIndex)
		self.panel.main._validate()

	def OnExpertOpen(self, e):
		from Cura.gui import expertConfig

		expert_sub_category = self.setting.getExpertSubCategory()
		if type(expert_sub_category) is list:
			expert_sub_category = expert_sub_category[self.ctrl.GetSelection()]
		ecw = expertConfig.expertConfigWindow(self.panel.main._callback, expert_sub_category)
		ecw.Centre()
		ecw.Show()

	def _validate(self):
		if type(self.setting.getExpertSubCategory()) is list:
			self._expert_button.Enable(self.setting.getExpertSubCategory()[self.ctrl.GetSelection()] is not None)
		result, msg = self.setting.validate()

		ctrl = self.ctrl
		if isinstance(ctrl, floatspin.FloatSpin):
			ctrl = ctrl.GetTextCtrl()
		if result == validators.ERROR:
			ctrl.SetBackgroundColour('Red')
		elif result == validators.WARNING:
			ctrl.SetBackgroundColour('Yellow')
		else:
			ctrl.SetBackgroundColour(self.defaultBGColour)
		ctrl.Refresh()

		self.validationMsg = msg

	def GetValue(self):
		if isinstance(self.ctrl, wx.ColourPickerCtrl):
			return str(self.ctrl.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
		elif isinstance(self.ctrl, wx.ComboBox):
			value = unicode(self.ctrl.GetValue())
			for ret in self._englishChoices:
				if _(ret) == value:
					return ret
			return value
		else:
			return str(self.ctrl.GetValue())

	def SetValue(self, value):
		if isinstance(self.ctrl, wx.CheckBox):
			self.ctrl.SetValue(str(value) == "True")
		elif isinstance(self.ctrl, wx.ColourPickerCtrl):
			self.ctrl.SetColour(value)
		elif isinstance(self.ctrl, floatspin.FloatSpin):
			try:
				self.ctrl.SetValue(float(value))
			except ValueError:
				pass
		elif isinstance(self.ctrl, wx.ComboBox):
			self.ctrl.SetValue(_(value))
		else:
			self.ctrl.SetValue(value)

class ToolHeadRow(object):
	def __init__(self, panel, configName, index = None):
		sizer = panel.GetSizer()
		x = sizer.GetRows()
		y = 0
		flag = 0

		self.setting = profile.settingsDictionary[configName]
		self.settingIndex = index
		self.validationMsg = ''
		self.panel = panel
		# We need a subpanel here because SettingRow always takes 2 grid spaces
		# and we shouldn't take more than that.
		self.subpanel = wx.Panel(self.panel)
		subsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.subpanel.SetSizer(subsizer)

		self.label = wx.lib.stattext.GenStaticText(panel, -1, self.setting.getLabel())
		self.label.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)

		self.ctrl = wx.TextCtrl(self.subpanel, -1, self.setting.getValue(self.settingIndex))
		self.ctrl.SetMinSize((300, 20))
		self.ctrl.Enable(False)

		self.button = wx.Button(self.subpanel, -1, _("Change Tool Head"))

		flag = wx.EXPAND
		self.ctrl.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
		subsizer.Add(self.ctrl, 1, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		subsizer.Add(self.button, 0, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT,border=2)

		sizer.Add(self.label, (x,y), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT,border=10)
		sizer.Add(self.subpanel, (x,y+1), flag=wx.ALIGN_CENTER_VERTICAL|flag)
		sizer.SetRows(x+1)

		panel.main.settingControlList.append(self)

	def OnMouseEnter(self, e):
		self.label.SetToolTipString(self.setting.getTooltip())
		self.ctrl.SetToolTipString(self.setting.getTooltip())
		e.Skip()

	def OnMouseExit(self, e):
		self.label.SetToolTipString('')
		self.ctrl.SetToolTipString('')
		e.Skip()

	def GetValue(self):
		return str(self.ctrl.GetValue())

	def SetValue(self, value):
		self.ctrl.SetValue(value)

	def _validate(self):
		pass


class PopUp(wx.Frame):
	def __init__(self, parent, id, text):
		wx.Frame.__init__(self, parent, id, 'Frame title', size=(400,300))
		panely = wx.Panel(self)		
		wx.StaticText(panely, -1, text, (10,10))
