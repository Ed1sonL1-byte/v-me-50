import { useEffect, useState } from "react";
import { ArrowUpRight, UserRound } from "lucide-react";
import { gateway, gatewayConfig } from "../../api/gateway";
import { webUrl } from "../../api/contracts";
import type { GatewayUser } from "../../api/contracts";

export function AccountButton() {
  const [user, setUser] = useState<GatewayUser | null>(null);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    void gateway
      .session(controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setUser(value);
      })
      .catch(() => {
        if (!controller.signal.aborted && gatewayConfig.sessionPath)
          setNotice(
            "We couldn’t check your sign-in status. You can try signing in again.",
          );
      });
    return () => controller.abort();
  }, []);

  function signIn() {
    const url = webUrl(gatewayConfig.loginUrl);
    if (url) window.location.assign(url);
    else
      setNotice(
        "Sign-in is not available yet. You can explore the sample in the meantime.",
      );
  }

  return (
    <div className="account">
      {user ? (
        <span className="account-name">
          <UserRound size={16} />
          {user.name || "Signed in"}
        </span>
      ) : (
        <button className="sign-in" onClick={signIn}>
          Sign in <ArrowUpRight size={15} />
        </button>
      )}
      {notice && (
        <div className="account-notice" role="status">
          <p>{notice}</p>
          <button
            onClick={() => setNotice("")}
            aria-label="Dismiss sign-in message"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
