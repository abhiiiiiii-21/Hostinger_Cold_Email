import re

with open("app/automation/page.tsx", "r") as f:
    text = f.read()

# 1. Replace the return statement top part
top_search = '  return (\n    <div className="h-screen w-full overflow-hidden bg-[#0c0c0e] text-zinc-300 flex flex-col font-sans selection:bg-zinc-200 selection:text-zinc-900">'
top_end = '        {/* LAUNCH CAMPAIGN & LOGS */}\n        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">'

start_idx = text.find(top_search)
end_idx = text.find(top_end)

if start_idx != -1 and end_idx != -1:
    new_top = """  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Automation Engine</h1>
        <p className="text-zinc-500 text-sm mt-1">Configure and launch your cold email campaigns.</p>
      </div>

      {/* LAUNCH CAMPAIGN & LOGS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">"""
    text = text[:start_idx] + new_top + text[end_idx + len(top_end):]
else:
    print("Could not find top section")

# 2. Replace the bottom part
bot_search = """            </div>
          </div>
        </div>
      </>
    ) : ("""

bot_idx = text.find(bot_search)
if bot_idx != -1:
    new_bot = """            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
"""
    text = text[:bot_idx] + new_bot
else:
    print("Could not find bottom section")

with open("app/automation/page.tsx", "w") as f:
    f.write(text)
print("done")
