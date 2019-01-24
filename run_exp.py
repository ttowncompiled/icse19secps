from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import pandas as pd
import random
import seaborn as sns

def run_trial(alpha, beta, n, uavs, victims, adj, turns, allow_collisions):
    """
        Executes a single trial of the experiment with the provided parameters.

        INPUT:
            alpha - The probability that the UAV's sensors detect a single victim in the same zone,
            beta - The probability that a victim remains in their current zone for the next turn,
            n - The number of zones in the city,
            uavs - A dictionary of ids to integers representing the zones of the
                UAVs initial deployment configuration,
            victims - A dictionary of ids to integers representing the zones of the
                victims initial deployment configuration,
            adj - A dictionary which takes a zone i and returns the zones adjacent to i,
            turns - The number of turns to run the trial, and
            allow_collisions - Whether or not collisions are permitted.
        OUTPUT:
            A list of the 4-tuples (alpha, beta, mission-effectiveness, num victims not found).
    """
    heatmap, eff = [ 1.0 / float(n) for _ in range(n) ], 0.0
    for t in range(turns):
        # system player turn
        sys_turn = []
        for u_zone in uavs:
            next_zone = u_zone
            # update location of UAV
            for a_j in adj[u_zone]:
                if heatmap[a_j] > heatmap[next_zone]:
                    if a_j in sys_turn and not allow_collisions:
                        continue
                    next_zone = a_j
            sys_turn.append(next_zone)
            # update heatmap after performing a scan
            heatmap[next_zone] = heatmap[next_zone] * (1 - alpha)
        uavs = sys_turn
        # update mission effectiveness
        eff = 1 - sum(heatmap)
        # environmental player turn
        env_turn = []
        for v_zone in victims:
            thwart = True
            for u_zone in uavs:
                if u_zone == v_zone:
                    # attempt to thwart scan
                    if random.uniform(0, 1) <= alpha:
                        thwart = False
            if not thwart:
                continue
            next_zone = v_zone
            # attempt to move the victim
            if random.uniform(0, 1) > beta:
                next_zone = random.choice(adj[v_zone])
            env_turn.append(next_zone)
        victims = env_turn
        # update the heatmap to account for the potential moves
        for i in range(n):
            heatmap[i] = heatmap[i] * beta
            for j in adj[i]:
                heatmap[i] += heatmap[j] * (1 - beta) * 1.0 / len(adj[j])
    return (alpha, beta, eff, len(victims))


def run_trials(uavs, victims, n, rows, cols, turns, adj, alphas, betas, trials, seed):
    random.seed(seed)
    r1, r2 = [], []
    for alpha in alphas:
        for beta in betas:
            for trial in range(trials):
                uav_conf = []
                for u_i in range(uavs):
                    uav_conf.append(random.randint(0, n-1))
                victim_conf = []
                for v_j in range(victims):
                    victim_conf.append(random.randint(0, n-1))
                trial_results = run_trial(alpha, beta, n, uav_conf, victim_conf,
                        adj, turns, True)
                r1.append(trial_results)
                trial_results = run_trial(alpha, beta, n, uav_conf, victim_conf,
                        adj, turns, False)
                r2.append(trial_results)
    return r1, r2


def graph_results(r1, r2, title, diff_only=False, set_lims=True):
    if not diff_only:
        data = []
        for p_i in r1:
            data.append([p_i[0], p_i[1], p_i[2]])
        df = pd.DataFrame(data, columns=['X', 'Y', 'Z'])
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.plot_trisurf(df['X'], df['Y'], df['Z'], cmap=plt.cm.jet, linewidth=0.01)
        ax.set_xlabel('alpha')
        ax.set_ylabel('beta')
        ax.set_zlabel('effectiveness')
        plt.show()
        plt.savefig(title + '.png')
    delta = []
    for i in range(len(r1)):
        t1, t2 = r1[i], r2[i]
        delta.append((t1[0], t1[1], t2[2]-t1[2], t2[3] - t1[3]))
    data = []
    for d_i in delta:
        data.append([d_i[0], d_i[1], d_i[2]])
    df = pd.DataFrame(data, columns=['X', 'Y', 'Z'])
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(df['X'], df['Y'], df['Z'], cmap=plt.cm.jet, linewidth=0.01)
    if set_lims:
        ax.set_zlim3d(-0.05, 0.05)
    ax.set_xlabel('alpha')
    ax.set_ylabel('beta')
    ax.set_zlabel('effectiveness')
    plt.show()
    plt.savefig(title + '.diff.png')


def main():
    seed = 695480078
    uavs = [4, 8, 16, 24, 32, 64, 128]
    victims = 10
    n, rows, cols = 164, 4, 41
    turns = 60
    adj = {}
    for i in range(n):
        adj_list = []
        if i // cols - 1 >= 0:
            adj_list.append( (i // cols - 1) * cols + i % cols )
        if (i + 1) % cols != 0:
            adj_list.append( i + 1 )
        if i // cols + 1 < rows:
            adj_list.append( (i // cols + 1) * cols + i % cols )
        if i % 41 != 0:
            adj_list.append( i - 1 )
        adj[i] = adj_list
    alphas = [ float(x+1) / 20.0 for x in range(20) ]
    betas = [ float(x+1) / 20.0 for x in range(20) ]
    trials = 1
    u1, u2 = run_trials(uavs[0], victims, n, rows, cols, turns, adj, alphas, betas, trials, seed)
    graph_results(u1, u2, 'fig.' + str(uavs[0]))
    for j in range(1, len(uavs)):
        r1, r2 = run_trials(uavs[j], victims, n, rows, cols, turns, adj, alphas, betas, trials, seed)
        graph_results(r1, r2, 'fig.' + str(uavs[j]))
        graph_results(u1, r1, 'fig.4.' + str(uavs[j]), diff_only=True, set_lims=False)


if __name__ == "__main__":
    main()
