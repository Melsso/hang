import type { FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/global/ToastProvider";

import { register } from "../api/auth";
import Button from "../components/global/Button";

import CountrySelect from "../components/profile/CountrySelect";
import InterestsSelect from "../components/profile/InterestsSelect";
import InterestedIn from "../components/profile/InterestedIn";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    interested_in: "",
    interests: [] as string[],
    country: "",
  });
  const { showToast } = useToast();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    const values = {
      ...Object.fromEntries(formData.entries()),
      interests: form.interests,
      country: form.country,
      interested_in: form.interested_in,
    };

    try {
      await register(values);
      showToast("Registered successfully.", "success");
      navigate("/login");
    } catch {
      showToast("Something went wrong, try again.", "error");
    }
  };

  const fieldClass =
    "w-full h-[44px] bg-[#222] text-white border border-[rgba(255,255,255,0.2)] rounded-[12px] px-[10px] outline-none focus:border-[rgba(255,255,255,0.4)]";
  const wrapperClass = "flex flex-col gap-2 w-full";
  const labelClass = "text-sm text-white/60";

  return (
    <div className="w-2/5 h-[60vh] flex flex-col items-center justify-start gap-4 border border-[rgba(255,255,255,0.06)] rounded-lg p-6 bg-[#111111]">
      <h2 className="card-header">Register</h2>

      <form onSubmit={handleSubmit} className="login-form">
        <div className={wrapperClass}>
          <label className={labelClass}>First Name</label>
          <input name="first_name" required className={fieldClass} />
        </div>

        <div className={wrapperClass}>
          <label className={labelClass}>Last Name</label>
          <input name="last_name" required className={fieldClass} />
        </div>

        <div className={wrapperClass}>
          <label className={labelClass}>Email</label>
          <input name="email" required className={fieldClass} />
        </div>

        <div className={wrapperClass}>
          <label className={labelClass}>Password</label>
          <input name="password" type="password" required className={fieldClass} />
        </div>

        <div className={wrapperClass}>
          <label className={labelClass}>Birthdate</label>
          <input name="birthdate" type="date" required className={fieldClass} />
        </div>

        <div className={wrapperClass}>
          <label className={labelClass}>Gender</label>
          <select name="gender" required defaultValue="" className={fieldClass}>
            <option value="" disabled>
              Select Gender
            </option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>

        <InterestedIn
          value={form.interested_in}
          setValue={(value) =>
            setForm((prev) => ({
              ...prev,
              interested_in: value,
            }))
          }
        />
        <InterestsSelect
          value={form.interests}
          onChange={(values) =>
            setForm((prev) => ({
              ...prev,
              interests: values,
            }))
          }
        />
        <CountrySelect
          value={form.country}
          onChange={(value) =>
            setForm((prev) => ({
              ...prev,
              country: value,
            }))
          }
        />

        <div className={wrapperClass}>
          <label className={labelClass}>Bio</label>
          <textarea
            name="bio"
            required
            className="w-full min-h-[120px] bg-[#222] text-white border border-[rgba(255,255,255,0.2)] rounded-[12px] px-[10px] py-[10px] outline-none focus:border-[rgba(255,255,255,0.4)]"
          />
        </div>

        <Button type="submit">Register</Button>
      </form>

      <Button
        className="oauth-btn"
        onClick={() => {
          window.location.href = "/api/auth/login/google";
        }}
      >
        Continue with Google
      </Button>

      <Button className="redir-btn" onClick={() => navigate("/login")}>
        Already have an account?
      </Button>
    </div>
  );
}
