import { BrowserRouter, Switch, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Query from './pages/Query';
import Entities from './pages/Entities';
import Analysis from './pages/Analysis';
import Temporal from './pages/Temporal';
import Geographic from './pages/Geographic';
import Sources from './pages/Sources';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Switch>
          <Route exact path="/" component={Dashboard} />
          <Route path="/query" component={Query} />
          <Route path="/entities" component={Entities} />
          <Route path="/analysis" component={Analysis} />
          <Route path="/temporal" component={Temporal} />
          <Route path="/map" component={Geographic} />
          <Route path="/sources" component={Sources} />
          <Route path="/alerts" component={Alerts} />
          <Route path="/settings" component={Settings} />
        </Switch>
      </Layout>
    </BrowserRouter>
  );
}
