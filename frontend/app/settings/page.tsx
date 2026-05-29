import { AppShell } from "@/components/shell/AppShell";

export const metadata = { title: "Settings – Senior Heat Voice Lab" };

const SECTIONS = [
  {
    title: "Notifications",
    fields: [
      { label: "Critical alert emails", type: "toggle", value: true },
      { label: "Missed check-in SMS", type: "toggle", value: true },
      { label: "Daily summary report", type: "toggle", value: false },
    ],
  },
  {
    title: "Check-in Defaults",
    fields: [
      { label: "Default call window start", type: "text", value: "9:00 AM" },
      { label: "Default call window end", type: "text", value: "1:00 PM" },
      { label: "Max retry attempts", type: "text", value: "3" },
    ],
  },
  {
    title: "Account",
    fields: [
      { label: "Display name", type: "text", value: "Jane Martinez" },
      { label: "Email", type: "text", value: "jane.martinez@example.com" },
      { label: "Role", type: "text", value: "Case Manager" },
    ],
  },
];

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="p-6 overflow-auto h-full">
        <div className="max-w-2xl">
          <div className="mb-6">
            <h1 className="font-bold text-2xl" style={{ color: "#071D3A" }}>
              Settings
            </h1>
            <p className="text-sm mt-1" style={{ color: "#667085" }}>
              Manage your account and notification preferences.
            </p>
          </div>

          <div className="space-y-6">
            {SECTIONS.map((section) => (
              <div
                key={section.title}
                className="rounded-lg"
                style={{ background: "white", border: "1px solid #D8E0EA" }}
              >
                <div
                  className="px-5 py-4 border-b"
                  style={{ borderColor: "#D8E0EA" }}
                >
                  <h2 className="font-semibold text-sm" style={{ color: "#071D3A" }}>
                    {section.title}
                  </h2>
                </div>
                <div className="px-5 py-4 space-y-4">
                  {section.fields.map((field) => (
                    <div key={field.label} className="flex items-center justify-between">
                      <label className="text-sm" style={{ color: "#071D3A" }}>
                        {field.label}
                      </label>
                      {field.type === "toggle" ? (
                        <div
                          className="rounded-full cursor-pointer transition-colors"
                          style={{
                            width: 40,
                            height: 22,
                            background: field.value ? "#22C7C9" : "#D8E0EA",
                            position: "relative",
                          }}
                        >
                          <span
                            className="rounded-full bg-white shadow"
                            style={{
                              position: "absolute",
                              top: 2,
                              left: field.value ? 20 : 2,
                              width: 18,
                              height: 18,
                              transition: "left 0.15s",
                              display: "block",
                            }}
                          />
                        </div>
                      ) : (
                        <input
                          type="text"
                          defaultValue={field.value as string}
                          className="rounded border px-3 py-1.5 text-sm outline-none focus:border-teal transition-colors"
                          style={{
                            borderColor: "#D8E0EA",
                            color: "#071D3A",
                            width: 200,
                          }}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}

            <div className="flex gap-3 pt-2">
              <button
                className="px-4 py-2 rounded text-sm font-medium text-white transition-colors"
                style={{ background: "#22C7C9" }}
              >
                Save Changes
              </button>
              <button
                className="px-4 py-2 rounded text-sm font-medium transition-colors"
                style={{ background: "#F8FAFC", color: "#667085", border: "1px solid #D8E0EA" }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
