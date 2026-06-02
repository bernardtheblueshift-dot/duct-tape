import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { api, APIError } from '@/lib/api';

export function RegisterPage() {
  const [name, setName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.auth.register({ email, password, name, company_name: companyName });
      setSuccess(true);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="w-full max-w-md p-8 space-y-6 bg-surface border border-border rounded-lg">
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">GT</h1>
            <p className="text-muted text-sm font-mono">crew management</p>
          </div>

          <div className="space-y-4 text-center">
            <div className="text-accent text-lg font-medium">Check your email</div>
            <p className="text-muted text-sm">
              We've sent a verification link to <span className="text-primary font-mono">{email}</span>
            </p>
            <p className="text-muted-foreground text-xs">
              Click the link in the email to activate your account.
            </p>
          </div>

          <div className="text-center text-sm text-muted">
            Already verified?{' '}
            <Link to="/login" className="text-accent hover:underline">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="w-full max-w-md p-8 space-y-6 bg-surface border border-border rounded-lg">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">GT</h1>
          <p className="text-muted text-sm font-mono">crew management</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="name" className="block text-sm font-medium">
              Your Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="Jane Smith"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="company" className="block text-sm font-medium">
              Company Name
            </label>
            <input
              id="company"
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="Acme Productions"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="email" className="block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="you@company.com"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="••••••••"
            />
            <p className="text-xs text-muted-foreground">Minimum 8 characters</p>
          </div>

          {error && (
            <div className="text-destructive text-sm p-2 bg-destructive/10 border border-destructive/20 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent hover:bg-accent/90 text-accent-foreground font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating account...' : 'Register'}
          </button>
        </form>

        <div className="text-center text-sm text-muted">
          Already have an account?{' '}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
