def calc_percent_change(previous, current):
    return (current - previous) / previous


# confirm the percent change!
fgrt=[0.2395000010728836, 0.23999999463558197, 0.24009999632835388, 0.2493000030517578, 0.2639999985694885]
m=min(fgrt)
print(f"min {m}")
print("percent: ", calc_percent_change(min(fgrt), fgrt[-1]))
